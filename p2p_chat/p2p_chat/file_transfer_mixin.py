"""
File transfer mixin for RTCPeer class.
Contains all file transfer related methods.
"""

import asyncio
import logging
import os
import json
import hashlib
import tempfile
from typing import Dict, Any, Optional

from .file_transfer import FileTransfer
from .security import (
    validate_file_transfer,
    FileSecurityViolation,
    calculate_file_checksum,
    verify_file_integrity
)
from .utils import get_executable_dir

logger = logging.getLogger(__name__)


class FileTransferMixin:
    """Mixin class containing file transfer functionality for RTCPeer."""
    
    def __init__(self):
        # File transfer management
        self.active_file_transfers: Dict[str, FileTransfer] = {}
        self.outgoing_file_transfer: Optional[FileTransfer] = None
        self.file_chunk_size = 32768  # 32KB chunks for better stability
        self.file_offer_timeout = 300.0  # 5 minutes timeout for file offer acceptance
        self.file_offer_timer: Optional[asyncio.Task] = None
    
    def _handle_file_control_message(self, data: Dict[str, Any]) -> None:
        """Handle file transfer control messages."""
        try:
            msg_type = data.get('type')
            
            if msg_type == 'file_offer':
                self._handle_file_offer(data)
            elif msg_type == 'file_accept':
                self._handle_file_accept(data)
            elif msg_type == 'file_reject':
                self._handle_file_reject(data)
            elif msg_type == 'file_timeout':
                self._handle_file_timeout(data)
            elif msg_type == 'file_start':
                self._handle_file_start(data)
            elif msg_type == 'file_end':
                self._handle_file_end(data)
            elif msg_type == 'file_error':
                self._handle_file_error(data)
            elif msg_type == 'file_cancel':
                self._handle_file_cancel(data)
            else:
                logger.warning(f"Unknown file control message type: {msg_type}")
                
        except Exception as e:
            logger.error(f"Error handling file control message: {e}")
            self.emit("file_error", f"File transfer error: {e}")
    
    def _handle_binary_message(self, data: bytes) -> None:
        """Handle incoming binary file chunk data."""
        try:
            # Find the active transfer that expects this chunk
            for transfer_id, transfer in self.active_file_transfers.items():
                if not transfer.is_complete and transfer.file_handle:
                    transfer.bytes_received += len(data)
                    
                    # Write chunk to temporary file
                    try:
                        transfer.file_handle.write(data)
                        # Flush every 5MB to balance performance and data safety
                        if transfer.bytes_received % (5 * 1024 * 1024) == 0:
                            transfer.file_handle.flush()
                    except Exception as e:
                        logger.error(f"Error writing chunk to file: {e}")
                        raise
                    
                    # Emit progress update every 1MB to reduce overhead
                    if transfer.bytes_received % (1024 * 1024) == 0:
                        progress = (transfer.bytes_received / transfer.file_size) * 100
                        self.emit("file_progress", {
                            'transfer_id': transfer_id,
                            'filename': transfer.filename,
                            'bytes_received': transfer.bytes_received,
                            'total_bytes': transfer.file_size,
                            'progress': progress
                        })
                    
                    # Check if transfer is complete
                    if transfer.bytes_received >= transfer.file_size:
                        logger.info(f"All chunks received for {transfer.filename}: {transfer.bytes_received}/{transfer.file_size} bytes")
                        
                        # Final progress update
                        self.emit("file_progress", {
                            'transfer_id': transfer_id,
                            'filename': transfer.filename,
                            'bytes_received': transfer.bytes_received,
                            'total_bytes': transfer.file_size,
                            'progress': 100.0
                        })
                        
                        self._complete_file_transfer(transfer_id)
                    
                    break
            else:
                logger.warning("Received file chunk but no active transfer found")
                logger.debug(f"Active transfers: {list(self.active_file_transfers.keys())}")
                
        except Exception as e:
            logger.error(f"Error handling binary message: {e}")
            self.emit("file_error", f"Error receiving file chunk: {e}")
    
    def _handle_file_offer(self, data: Dict[str, Any]) -> None:
        """Handle incoming file transfer offer."""
        try:
            filename = data.get('filename')
            file_size = data.get('file_size')
            checksum = data.get('checksum')
            transfer_id = data.get('transfer_id')
            
            if not all([filename, file_size, checksum, transfer_id]):
                raise ValueError("Invalid file offer data")
            
            # Enable file operation mode for aggressive heartbeat
            if hasattr(self, 'peer') and hasattr(self.peer, 'enable_file_operation_mode'):
                self.peer.enable_file_operation_mode()
            
            # Validate the file transfer (allow any file type and size)
            sanitized_filename = validate_file_transfer(filename, file_size, allow_any_extension=True)
            
            # Create transfer object for tracking
            transfer = FileTransfer(sanitized_filename, file_size, checksum, transfer_id)
            self.active_file_transfers[transfer_id] = transfer
            
            # Emit file offer event for user approval
            self.emit("file_offer", {
                'filename': sanitized_filename,
                'file_size': file_size,
                'transfer_id': transfer_id,
                'checksum': checksum
            })
            
        except (FileSecurityViolation, ValueError) as e:
            logger.error(f"File offer validation failed: {e}")
            # Send rejection
            self._send_file_control({
                'type': 'file_reject',
                'transfer_id': data.get('transfer_id'),
                'reason': str(e)
            })
    
    def _handle_file_accept(self, data: Dict[str, Any]) -> None:
        """Handle file transfer acceptance."""
        transfer_id = data.get('transfer_id')
        if transfer_id and self.outgoing_file_transfer and self.outgoing_file_transfer.transfer_id == transfer_id:
            logger.info(f"File transfer accepted: {transfer_id}")
            
            # Cancel timeout timer
            if self.file_offer_timer:
                self.file_offer_timer.cancel()
                self.file_offer_timer = None
            
            self.emit("file_accepted", {'transfer_id': transfer_id})
            # Start sending the file
            asyncio.create_task(self._send_file_chunks())
        else:
            logger.warning(f"Received file accept for unknown transfer: {transfer_id}")
    
    def _handle_file_reject(self, data: Dict[str, Any]) -> None:
        """Handle file transfer rejection."""
        transfer_id = data.get('transfer_id')
        reason = data.get('reason', 'No reason provided')
        logger.info(f"File transfer rejected: {transfer_id}, reason: {reason}")
        
        # Cancel timeout timer
        if self.file_offer_timer:
            self.file_offer_timer.cancel()
            self.file_offer_timer = None
        
        # Clean up outgoing transfer
        if self.outgoing_file_transfer and self.outgoing_file_transfer.transfer_id == transfer_id:
            self.outgoing_file_transfer = None
        
        self.emit("file_rejected", {'transfer_id': transfer_id, 'reason': reason})
    
    def _handle_file_start(self, data: Dict[str, Any]) -> None:
        """Handle file transfer start signal."""
        transfer_id = data.get('transfer_id')
        if transfer_id in self.active_file_transfers:
            transfer = self.active_file_transfers[transfer_id]
            logger.info(f"File transfer started: {transfer.filename}")
            self.emit("file_started", {
                'transfer_id': transfer_id,
                'filename': transfer.filename
            })
    
    def _handle_file_end(self, data: Dict[str, Any]) -> None:
        """Handle file transfer completion signal."""
        transfer_id = data.get('transfer_id')
        if transfer_id in self.active_file_transfers:
            self._complete_file_transfer(transfer_id)
    
    def _handle_file_error(self, data: Dict[str, Any]) -> None:
        """Handle file transfer error."""
        transfer_id = data.get('transfer_id')
        error_msg = data.get('error', 'Unknown error')
        logger.error(f"File transfer error for {transfer_id}: {error_msg}")
        self.emit("file_error", {'transfer_id': transfer_id, 'error': error_msg})
        
        # Clean up transfer
        if transfer_id in self.active_file_transfers:
            self._cleanup_file_transfer(transfer_id)
    
    def _handle_file_cancel(self, data: Dict[str, Any]) -> None:
        """Handle file transfer cancellation."""
        transfer_id = data.get('transfer_id')
        logger.info(f"File transfer cancelled: {transfer_id}")
        self.emit("file_cancelled", {'transfer_id': transfer_id})
        
        # Clean up
        if transfer_id in self.active_file_transfers:
            self._cleanup_file_transfer(transfer_id)
        if self.outgoing_file_transfer and self.outgoing_file_transfer.transfer_id == transfer_id:
            self.outgoing_file_transfer = None
    
    def _complete_file_transfer(self, transfer_id: str) -> None:
        """Complete an incoming file transfer."""
        try:
            transfer = self.active_file_transfers.get(transfer_id)
            if not transfer:
                logger.error(f"Transfer not found for ID: {transfer_id}")
                return
            
            # Check if transfer is already complete to prevent duplicate processing
            if transfer.is_complete:
                logger.info(f"Transfer {transfer_id} already completed, skipping duplicate completion")
                return
            
            logger.info(f"Completing file transfer: {transfer.filename}, temp_path: {transfer.temp_path}")
            
            # Flush and close file handle
            if transfer.file_handle:
                try:
                    transfer.file_handle.flush()  # Ensure all data is written to disk
                    os.fsync(transfer.file_handle.fileno())  # Force write to disk
                    transfer.file_handle.close()
                    transfer.file_handle = None
                    logger.info(f"File handle closed and flushed for: {transfer.filename}")
                except Exception as e:
                    logger.error(f"Error closing file handle: {e}")
            
            # Verify file integrity
            if transfer.temp_path:
                if os.path.exists(transfer.temp_path):
                    file_size = os.path.getsize(transfer.temp_path)
                    logger.info(f"Temp file exists: {transfer.temp_path}, size: {file_size} bytes")
                    
                    if verify_file_integrity(transfer.temp_path, transfer.checksum):
                        transfer.is_complete = True  # Mark as complete before emitting event
                        logger.info(f"File transfer completed successfully: {transfer.filename}")
                        
                        # Emit completion event with temp file path
                        self.emit("file_completed", {
                            'transfer_id': transfer_id,
                            'filename': transfer.filename,
                            'temp_path': transfer.temp_path,
                            'save_path': transfer.save_path,  # Include user's chosen save location
                            'file_size': transfer.file_size
                        })
                    else:
                        raise FileSecurityViolation("File integrity check failed")
                else:
                    logger.error(f"Temporary file not found at: {transfer.temp_path}")
                    # List files in executable directory for debugging
                    temp_dir = get_executable_dir()
                    try:
                        temp_files = os.listdir(temp_dir)
                        p2p_files = [f for f in temp_files if 'p2p_transfer' in f]
                        logger.info(f"P2P temp files in {temp_dir}: {p2p_files}")
                    except Exception as e:
                        logger.warning(f"Could not list executable directory: {e}")
                    
                    raise FileSecurityViolation(f"Temporary file not found at: {transfer.temp_path}")
            else:
                raise FileSecurityViolation("No temporary file path set")
                
        except Exception as e:
            logger.error(f"Error completing file transfer: {e}")
            self.emit("file_error", {'transfer_id': transfer_id, 'error': str(e)})
            self._cleanup_file_transfer(transfer_id)
    
    def _send_file_control(self, data: Dict[str, Any]) -> None:
        """Send a file transfer control message."""
        if self.channel and self.channel.readyState == "open":
            try:
                message = json.dumps(data)
                self.channel.send(message)
            except Exception as e:
                logger.error(f"Error sending file control message: {e}")
    
    async def _send_file_chunks(self) -> None:
        """Send file chunks for outgoing transfer."""
        if not self.outgoing_file_transfer:
            return
        
        transfer = self.outgoing_file_transfer
        
        try:
            # Send file start signal
            self._send_file_control({
                'type': 'file_start',
                'transfer_id': transfer.transfer_id
            })
            
            # Open and send file in chunks
            with open(transfer.temp_path, 'rb') as f:
                bytes_sent = 0
                chunk_count = 0
                
                while True:
                    # Check connection before each chunk
                    if not self.channel or self.channel.readyState != "open":
                        raise Exception("Data channel closed during transfer")
                    
                    chunk = f.read(self.file_chunk_size)
                    if not chunk:
                        break
                    
                    try:
                        # Send binary chunk
                        self.channel.send(chunk)
                        bytes_sent += len(chunk)
                        chunk_count += 1
                        
                        # Emit progress every 10 chunks to reduce overhead
                        if chunk_count % 10 == 0:
                            progress = (bytes_sent / transfer.file_size) * 100
                            self.emit("file_send_progress", {
                                'transfer_id': transfer.transfer_id,
                                'filename': transfer.filename,
                                'bytes_sent': bytes_sent,
                                'total_bytes': transfer.file_size,
                                'progress': progress
                            })
                        
                        # Send keepalive every 25 chunks to prevent connection timeout
                        if chunk_count % 25 == 0 and self.channel and self.channel.readyState == "open":
                            try:
                                keepalive_msg = json.dumps({
                                    "type": "file_keepalive",
                                    "transfer_id": transfer.transfer_id,
                                    "timestamp": asyncio.get_event_loop().time()
                                })
                                self.channel.send(keepalive_msg)
                            except Exception as e:
                                logger.warning(f"Failed to send file keepalive: {e}")
                        
                        # Adaptive delay based on file size to prevent overwhelming
                        if transfer.file_size > 100 * 1024 * 1024:  # > 100MB
                            await asyncio.sleep(0.08)  # 80ms for large files
                        elif transfer.file_size > 10 * 1024 * 1024:  # > 10MB
                            await asyncio.sleep(0.06)  # 60ms for medium files
                        else:
                            await asyncio.sleep(0.04)  # 40ms for smaller files
                        
                    except Exception as e:
                        logger.error(f"Error sending file chunk {chunk_count}: {e}")
                        raise
            
            # Send completion signal
            self._send_file_control({
                'type': 'file_end',
                'transfer_id': transfer.transfer_id
            })
            
            logger.info(f"File sent successfully: {transfer.filename}")
            self.emit("file_sent", {
                'transfer_id': transfer.transfer_id,
                'filename': transfer.filename
            })
            
            # Clean up
            self.outgoing_file_transfer = None
            
        except Exception as e:
            logger.error(f"Error sending file: {e}")
            self._send_file_control({
                'type': 'file_error',
                'transfer_id': transfer.transfer_id,
                'error': str(e)
            })
            self.emit("file_error", {'transfer_id': transfer.transfer_id, 'error': str(e)})
            self.outgoing_file_transfer = None
    
    def _cleanup_file_transfer(self, transfer_id: str) -> None:
        """Clean up a specific file transfer."""
        transfer = self.active_file_transfers.get(transfer_id)
        if transfer:
            if transfer.file_handle:
                transfer.file_handle.close()
            if transfer.temp_path and os.path.exists(transfer.temp_path):
                try:
                    os.remove(transfer.temp_path)
                except Exception as e:
                    logger.warning(f"Could not remove temp file: {e}")
            del self.active_file_transfers[transfer_id]
    
    def _cleanup_file_transfers(self) -> None:
        """Clean up all active file transfers."""
        for transfer_id in list(self.active_file_transfers.keys()):
            self._cleanup_file_transfer(transfer_id)
        
        if self.outgoing_file_transfer:
            self.outgoing_file_transfer = None
        
        # Disable file operation mode if no active transfers
        if not self.active_file_transfers and not self.outgoing_file_transfer:
            if hasattr(self, 'peer') and hasattr(self.peer, 'disable_file_operation_mode'):
                self.peer.disable_file_operation_mode()
    
    # Public file transfer methods
    
    def send_file(self, file_path: str) -> str:
        """
        Initiate a file transfer.
        
        Args:
            file_path: Path to the file to send
            
        Returns:
            Transfer ID for tracking
            
        Raises:
            FileSecurityViolation: If file validation fails
            Exception: If transfer cannot be initiated
        """
        if not self.is_connected:
            raise Exception("Cannot send file: not connected to peer")
        
        if self.outgoing_file_transfer:
            raise Exception("Another file transfer is already in progress")
        
        try:
            # Validate file
            if not os.path.exists(file_path):
                raise FileSecurityViolation("File does not exist")
            
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            
            # Security validation (allow any file type and size)
            sanitized_filename = validate_file_transfer(filename, file_size, allow_any_extension=True)
            
            # Enable file operation mode for aggressive heartbeat
            if hasattr(self, 'peer') and hasattr(self.peer, 'enable_file_operation_mode'):
                self.peer.enable_file_operation_mode()
            
            # Calculate checksum
            checksum = calculate_file_checksum(file_path)
            
            # Generate transfer ID
            transfer_id = hashlib.md5(f"{filename}{file_size}{checksum}".encode()).hexdigest()
            
            # Create transfer object
            self.outgoing_file_transfer = FileTransfer(
                sanitized_filename, file_size, checksum, transfer_id
            )
            self.outgoing_file_transfer.temp_path = file_path
            
            # Send file offer
            self._send_file_control({
                'type': 'file_offer',
                'filename': sanitized_filename,
                'file_size': file_size,
                'checksum': checksum,
                'transfer_id': transfer_id
            })
            
            # Start timeout timer for file offer acceptance
            self._start_file_offer_timeout(transfer_id)
            
            logger.info(f"File transfer initiated: {sanitized_filename} ({file_size} bytes)")
            return transfer_id
            
        except Exception as e:
            logger.error(f"Failed to initiate file transfer: {e}")
            self.outgoing_file_transfer = None
            raise
    
    def accept_file(self, transfer_id: str, save_path: str) -> None:
        """
        Accept an incoming file transfer.
        
        Args:
            transfer_id: ID of the transfer to accept
            save_path: Directory to save the file
        """
        try:
            # Create temporary file for receiving in executable directory
            temp_dir = get_executable_dir()
            temp_path = temp_dir / f"p2p_transfer_{transfer_id}"
            
            # Create transfer object
            # Note: We'll get the details from the file offer event
            if transfer_id not in self.active_file_transfers:
                # This should have been created during file offer handling
                raise Exception("Transfer ID not found")
            
            transfer = self.active_file_transfers[transfer_id]
            transfer.temp_path = str(temp_path)
            transfer.file_handle = open(temp_path, 'wb')
            transfer.save_path = save_path  # Store user's chosen save location
            
            # Send acceptance
            self._send_file_control({
                'type': 'file_accept',
                'transfer_id': transfer_id
            })
            
            logger.info(f"File transfer accepted: {transfer_id}")
            
        except Exception as e:
            logger.error(f"Failed to accept file transfer: {e}")
            self._send_file_control({
                'type': 'file_reject',
                'transfer_id': transfer_id,
                'reason': str(e)
            })
    
    def reject_file(self, transfer_id: str, reason: str = "User declined") -> None:
        """
        Reject an incoming file transfer.
        
        Args:
            transfer_id: ID of the transfer to reject
            reason: Reason for rejection
        """
        self._send_file_control({
            'type': 'file_reject',
            'transfer_id': transfer_id,
            'reason': reason
        })
        
        # Clean up if exists
        if transfer_id in self.active_file_transfers:
            self._cleanup_file_transfer(transfer_id)
    
    def cancel_file_transfer(self, transfer_id: str) -> None:
        """
        Cancel an active file transfer.
        
        Args:
            transfer_id: ID of the transfer to cancel
        """
        self._send_file_control({
            'type': 'file_cancel',
            'transfer_id': transfer_id
        })
        
        # Clean up
        if transfer_id in self.active_file_transfers:
            self._cleanup_file_transfer(transfer_id)
        if self.outgoing_file_transfer and self.outgoing_file_transfer.transfer_id == transfer_id:
            self.outgoing_file_transfer = None
    
    def _start_file_offer_timeout(self, transfer_id: str) -> None:
        """Start timeout timer for file offer acceptance."""
        if self.file_offer_timer:
            self.file_offer_timer.cancel()
        
        self.file_offer_timer = asyncio.create_task(self._file_offer_timeout_handler(transfer_id))
    
    async def _file_offer_timeout_handler(self, transfer_id: str) -> None:
        """Handle file offer timeout."""
        try:
            await asyncio.sleep(self.file_offer_timeout)
            
            # Check if transfer is still pending
            if (self.outgoing_file_transfer and 
                self.outgoing_file_transfer.transfer_id == transfer_id):
                
                logger.warning(f"File offer timeout for transfer {transfer_id}")
                
                # Send timeout notification to peer
                self._send_file_control({
                    'type': 'file_timeout',
                    'transfer_id': transfer_id,
                    'reason': 'Receiver took too long to accept the file transfer'
                })
                
                # Clean up outgoing transfer
                self.outgoing_file_transfer = None
                
                # Emit timeout event
                self.emit("file_timeout", {
                    'transfer_id': transfer_id,
                    'reason': 'File transfer offer timed out - receiver took too long to accept'
                })
                
        except asyncio.CancelledError:
            logger.debug("File offer timeout cancelled")
        except Exception as e:
            logger.error(f"Error in file offer timeout handler: {e}")
    
    def _handle_file_timeout(self, data: Dict[str, Any]) -> None:
        """Handle file transfer timeout notification."""
        transfer_id = data.get('transfer_id')
        reason = data.get('reason', 'Unknown timeout')
        
        logger.info(f"File transfer timeout received: {transfer_id}, reason: {reason}")
        
        # Clean up any active transfers for this ID
        if transfer_id in self.active_file_transfers:
            transfer = self.active_file_transfers[transfer_id]
            if transfer.file_handle:
                transfer.file_handle.close()
            del self.active_file_transfers[transfer_id]
        
        # Emit timeout event
        self.emit("file_timeout", {
            'transfer_id': transfer_id,
            'reason': reason
        }) 
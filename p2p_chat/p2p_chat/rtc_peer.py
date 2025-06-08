"""
WebRTC peer connection wrapper using aiortc.
Handles peer-to-peer connection establishment and data channel communication.
"""

import asyncio
import logging
import json
from typing import Optional, Callable, Dict, Any
from aiortc import RTCPeerConnection, RTCDataChannel, RTCSessionDescription, RTCConfiguration, RTCIceServer
from pyee.asyncio import AsyncIOEventEmitter

from .signaling import encode, decode
from .security import (
    sanitize_message, 
    validate_invite_key, 
    SecurityViolation,
    log_security_status,
    get_connection_security_info,
    verify_perfect_forward_secrecy
)
from .file_transfer_mixin import FileTransferMixin
from .voice_chat_mixin import VoiceChatMixin

logger = logging.getLogger(__name__)


class RTCPeer(AsyncIOEventEmitter, FileTransferMixin, VoiceChatMixin):
    """
    WebRTC peer connection wrapper for P2P chat communication.
    
    Handles connection establishment, data channel setup, message routing, file transfers, and voice chat.
    Uses Google's STUN server for NAT traversal.
    Includes automatic reconnection functionality for handling network issues.
    """
    
    def __init__(self):
        AsyncIOEventEmitter.__init__(self)
        FileTransferMixin.__init__(self)
        VoiceChatMixin.__init__(self)
        self.pc: Optional[RTCPeerConnection] = None
        self.channel: Optional[RTCDataChannel] = None
        self.is_initiator: bool = False
        
        # Reconnection state
        self.original_offer: Optional[RTCSessionDescription] = None
        self.original_answer: Optional[RTCSessionDescription] = None
        self.reconnection_enabled: bool = True
        self.reconnection_attempts: int = 0
        self.max_reconnection_attempts: int = 5
        self.reconnection_delay: float = 2.0  # Start with 2 seconds
        self.max_reconnection_delay: float = 30.0  # Max 30 seconds
        self.reconnection_task: Optional[asyncio.Task] = None
        self.connection_timeout: float = 15.0  # Timeout for connection establishment
        self.heartbeat_interval: float = 1.0  # Send heartbeat every 1 second to prevent ICE consent timeout
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.last_heartbeat_response: float = 0.0
        
        self._setup_peer_connection()
    
    def _setup_peer_connection(self) -> None:
        """Initialize the RTCPeerConnection with STUN configuration."""
        # Create RTCIceServer objects for STUN server
        ice_servers = [RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
        
        # Create RTCConfiguration object
        config = RTCConfiguration(iceServers=ice_servers)
        
        self.pc = RTCPeerConnection(configuration=config)
        
        # Set up event handlers
        self.pc.on("connectionstatechange", self._on_connection_state_change)
        self.pc.on("icegatheringstatechange", self._on_ice_gathering_state_change)
        self.pc.on("datachannel", self._on_datachannel)
        self.pc.on("track", self._on_track)  # Add track handler for voice chat
        
        logger.info("RTCPeerConnection initialized with STUN server")
    
    async def _on_connection_state_change(self) -> None:
        """Handle connection state changes."""
        if not self.pc:
            return
            
        state = self.pc.connectionState
        logger.info(f"Connection state changed to: {state}")
        
        if state == "connected":
            self.emit("connected")
            # Reset reconnection attempts on successful connection
            self.reconnection_attempts = 0
            self.reconnection_delay = 2.0
            # Log security status when connection is established
            log_security_status(self.pc)
            # Start heartbeat
            await self._start_heartbeat()
            
            # Add audio track if voice chat is enabled
            if self.voice_enabled:
                await self._add_audio_track()
                
        elif state == "closed":
            self.emit("closed")
            # Clean up any active file transfers
            self._cleanup_file_transfers()
            # Clean up voice chat
            await self._cleanup_voice_chat()
            await self._stop_heartbeat()
            await self._stop_reconnection()
        elif state == "failed":
            logger.error("WebRTC connection failed")
            self.emit("failed", "Connection failed - check network connectivity")
            self._cleanup_file_transfers()
            await self._cleanup_voice_chat()
            await self._stop_heartbeat()
            # Attempt reconnection if enabled
            if self.reconnection_enabled and (self.original_offer or self.original_answer):
                await self._attempt_reconnection()
        elif state == "disconnected":
            logger.warning("WebRTC connection disconnected")
            self.emit("disconnected")
            await self._stop_heartbeat()
            # Attempt reconnection if enabled
            if self.reconnection_enabled and (self.original_offer or self.original_answer):
                await self._attempt_reconnection()
    
    async def _on_ice_gathering_state_change(self) -> None:
        """Handle ICE gathering state changes."""
        if not self.pc:
            return
            
        state = self.pc.iceGatheringState
        logger.debug(f"ICE gathering state: {state}")
    
    async def _on_datachannel(self, channel: RTCDataChannel) -> None:
        """Handle incoming data channel from remote peer."""
        logger.info(f"Received data channel: {channel.label}, state: {channel.readyState}")
        self.channel = channel
        self._setup_data_channel()
    
    async def _on_track(self, track) -> None:
        """Handle incoming media track from remote peer."""
        logger.info(f"Received {track.kind} track")
        
        if track.kind == "audio":
            # Handle incoming audio track for voice chat
            self._setup_audio_track_handler(track)
            self.emit("voice_track_received", track)
        else:
            logger.warning(f"Received unsupported track type: {track.kind}")
    
    def _setup_data_channel(self) -> None:
        """Set up data channel event handlers."""
        if not self.channel:
            logger.error("Cannot setup data channel: channel is None")
            return
            
        logger.info(f"Setting up data channel '{self.channel.label}', current state: {self.channel.readyState}")
        
        @self.channel.on("open")
        def on_open():
            logger.info(f"Data channel '{self.channel.label}' opened")
            self.emit("channel_open")
        
        @self.channel.on("message")
        def on_message(message):
            logger.debug(f"Received message on '{self.channel.label}': {type(message)}")
            if isinstance(message, str):
                # Handle text messages and file transfer control messages
                self._handle_text_message(message)
            elif isinstance(message, bytes):
                # Handle binary file chunk data
                self._handle_binary_message(message)
            else:
                logger.warning(f"Received unknown message type: {type(message)}")
        
        @self.channel.on("close")
        def on_close():
            logger.info(f"Data channel '{self.channel.label}' closed")
            self.emit("channel_close")
            self._cleanup_file_transfers()
        
        # If channel is already open, emit the event immediately
        if self.channel.readyState == "open":
            logger.info(f"Data channel '{self.channel.label}' already open, emitting event")
            self.emit("channel_open")
    
    def _handle_text_message(self, message: str) -> None:
        """Handle text messages including file transfer control messages."""
        try:
            # Try to parse as JSON for file transfer control messages
            data = json.loads(message)
            if isinstance(data, dict) and 'type' in data:
                if data['type'] == 'heartbeat':
                    # Send heartbeat response
                    response = json.dumps({
                        "type": "heartbeat_response",
                        "timestamp": asyncio.get_event_loop().time()
                    })
                    if self.channel and self.channel.readyState == "open":
                        try:
                            self.channel.send(response)
                        except Exception as e:
                            logger.error(f"Failed to send heartbeat response: {e}")
                elif data['type'] == 'heartbeat_response':
                    # Update last heartbeat response time
                    self.last_heartbeat_response = asyncio.get_event_loop().time()
                else:
                    # Handle file transfer control messages
                    self._handle_file_control_message(data)
            else:
                # Regular chat message
                self.emit("message", message)
        except json.JSONDecodeError:
            # Regular chat message
            self.emit("message", message)
        except Exception as e:
            logger.error(f"Error handling text message: {e}")
            self.emit("error", f"Error handling message: {e}")
    
    async def create_initiator(self) -> str:
        """
        Create a new chat as the initiator.
        
        Returns:
            Base64-encoded invite key to share with the other peer
        """
        try:
            self.is_initiator = True
            
            # Create data channel
            logger.info("Creating data channel for initiator")
            self.channel = self.pc.createDataChannel("chat", ordered=True)
            logger.info(f"Created data channel, initial state: {self.channel.readyState}")
            self._setup_data_channel()
            
            # Create offer
            logger.info("Creating offer...")
            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)
            
            # Store original offer for reconnection
            self.original_offer = offer
            
            # Wait for ICE gathering to complete
            logger.info("Waiting for ICE gathering...")
            await self._wait_for_ice_gathering()
            
            # Encode and return the invite key
            invite_key = encode(self.pc.localDescription)
            logger.info("Created invite key successfully")
            return invite_key
            
        except Exception as e:
            logger.error(f"Failed to create initiator: {e}")
            self.emit("error", f"Failed to create chat: {e}")
            raise
    
    async def accept_invite(self, invite_key: str) -> str:
        """
        Accept an invitation to join a chat.
        
        Args:
            invite_key: Base64-encoded invite key from the initiator
            
        Returns:
            Base64-encoded return key to send back to the initiator
        """
        try:
            self.is_initiator = False
            
            # Validate and sanitize the invite key
            try:
                invite_key = validate_invite_key(invite_key)
                logger.info("Invite key validation passed")
            except SecurityViolation as e:
                logger.error(f"Invite key validation failed: {e}")
                self.emit("error", f"Invalid invite key: {e}")
                raise
            
            # Decode the invite key
            offer_data = decode(invite_key)
            offer = RTCSessionDescription(**offer_data)
            
            # Store original remote offer for reconnection
            self.original_remote_offer = offer
            
            # Set remote description
            await self.pc.setRemoteDescription(offer)
            
            # Create answer
            answer = await self.pc.createAnswer()
            await self.pc.setLocalDescription(answer)
            
            # Store original answer for reconnection
            self.original_answer = answer
            
            # Wait for ICE gathering to complete
            await self._wait_for_ice_gathering()
            
            # Encode and return the return key
            return_key = encode(self.pc.localDescription)
            logger.info("Created return key successfully")
            return return_key
            
        except SecurityViolation:
            # Re-raise security violations
            raise
        except Exception as e:
            logger.error(f"Failed to accept invite: {e}")
            self.emit("error", f"Failed to join chat: {e}")
            raise
    
    async def receive_return_key(self, return_key: str) -> None:
        """
        Complete the handshake by receiving the return key from the joiner.
        
        Args:
            return_key: Base64-encoded return key from the joiner
        """
        try:
            if not self.is_initiator:
                raise ValueError("Only the initiator can receive return keys")
            
            # Validate and sanitize the return key
            try:
                return_key = validate_invite_key(return_key)
                logger.info("Return key validation passed")
            except SecurityViolation as e:
                logger.error(f"Return key validation failed: {e}")
                self.emit("error", f"Invalid return key: {e}")
                raise
            
            # Decode the return key
            answer_data = decode(return_key)
            answer = RTCSessionDescription(**answer_data)
            
            # Store original remote answer for reconnection
            self.original_remote_answer = answer
            
            # Set remote description
            await self.pc.setRemoteDescription(answer)
            
            logger.info("Handshake completed successfully")
            
        except SecurityViolation:
            # Re-raise security violations
            raise
        except Exception as e:
            logger.error(f"Failed to receive return key: {e}")
            self.emit("error", f"Failed to complete handshake: {e}")
            raise
    
    async def _wait_for_ice_gathering(self, timeout: float = 10.0) -> None:
        """Wait for ICE gathering to complete."""
        if not self.pc:
            logger.warning("Cannot wait for ICE gathering: peer connection is None")
            return
            
        if self.pc.iceGatheringState == "complete":
            return
            
        # Wait for ICE gathering to complete
        start_time = asyncio.get_event_loop().time()
        while self.pc and self.pc.iceGatheringState != "complete":
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.warning(f"ICE gathering timeout after {timeout}s")
                break
            await asyncio.sleep(0.1)
    
    def send(self, message: str) -> None:
        """
        Send a message to the remote peer.
        
        Args:
            message: The message to send
        """
        if not self.channel or self.channel.readyState != "open":
            logger.error("Cannot send message: data channel not open")
            self.emit("error", "Cannot send message: not connected")
            return
        
        try:
            # Sanitize message before sending
            try:
                sanitized_message = sanitize_message(message)
                logger.debug("Message sanitization passed")
            except SecurityViolation as e:
                logger.error(f"Message sanitization failed: {e}")
                self.emit("error", f"Invalid message: {e}")
                return
            
            self.channel.send(sanitized_message)
            logger.debug(f"Sent message: {sanitized_message}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.emit("error", f"Failed to send message: {e}")
    
    async def close(self) -> None:
        """Close the peer connection and clean up resources."""
        try:
            # Disable reconnection
            self.reconnection_enabled = False
            
            # Stop reconnection and heartbeat tasks
            await self._stop_reconnection()
            await self._stop_heartbeat()
            
            if self.channel:
                self.channel.close()
                self.channel = None
            
            if self.pc:
                await self.pc.close()
                self.pc = None
            
            logger.info("RTCPeer closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing RTCPeer: {e}")
    
    @property
    def connection_state(self) -> str:
        """Get the current connection state."""
        return self.pc.connectionState if self.pc else "closed"
    
    @property
    def is_connected(self) -> bool:
        """Check if the peer is connected."""
        return (self.pc and 
                self.pc.connectionState == "connected" and
                self.channel and 
                self.channel.readyState == "open")
    
    async def _attempt_reconnection(self) -> None:
        """Attempt to reconnect using stored connection information."""
        if self.reconnection_task and not self.reconnection_task.done():
            logger.debug("Reconnection already in progress")
            return
            
        if self.reconnection_attempts >= self.max_reconnection_attempts:
            logger.error(f"Max reconnection attempts ({self.max_reconnection_attempts}) reached")
            self.emit("reconnection_failed", "Maximum reconnection attempts exceeded")
            return
        
        self.reconnection_attempts += 1
        logger.info(f"Attempting reconnection {self.reconnection_attempts}/{self.max_reconnection_attempts}")
        self.emit("reconnection_attempt", self.reconnection_attempts)
        
        # Create reconnection task
        self.reconnection_task = asyncio.create_task(self._perform_reconnection())
    
    async def _perform_reconnection(self) -> None:
        """Perform the actual reconnection logic."""
        try:
            # Wait before attempting reconnection (exponential backoff)
            await asyncio.sleep(self.reconnection_delay)
            self.reconnection_delay = min(self.reconnection_delay * 1.5, self.max_reconnection_delay)
            
            # Close existing connection
            if self.pc:
                await self.pc.close()
            
            # Create new peer connection
            self._setup_peer_connection()
            
            # Re-establish connection using stored information
            if self.is_initiator and self.original_offer:
                await self._reconnect_as_initiator()
            elif not self.is_initiator and self.original_answer:
                await self._reconnect_as_joiner()
            else:
                logger.error("Cannot reconnect: missing original connection info")
                self.emit("reconnection_failed", "Missing connection information")
                
        except Exception as e:
            logger.error(f"Reconnection attempt failed: {e}")
            # Schedule next attempt if we haven't exceeded max attempts
            if self.reconnection_attempts < self.max_reconnection_attempts:
                await asyncio.sleep(1.0)  # Brief delay before next attempt
                await self._attempt_reconnection()
            else:
                self.emit("reconnection_failed", str(e))
    
    async def _reconnect_as_initiator(self) -> None:
        """Reconnect as the original initiator."""
        logger.info("Reconnecting as initiator...")
        
        # Create new data channel
        self.channel = self.pc.createDataChannel("chat", ordered=True)
        self._setup_data_channel()
        
        # Set the original offer as local description
        await self.pc.setLocalDescription(self.original_offer)
        
        # Wait for ICE gathering with timeout
        try:
            await asyncio.wait_for(self._wait_for_ice_gathering(), timeout=self.connection_timeout)
            logger.info("Reconnection successful (initiator)")
        except asyncio.TimeoutError:
            logger.error("Reconnection timeout (initiator)")
            raise Exception("Reconnection timeout")
    
    async def _reconnect_as_joiner(self) -> None:
        """Reconnect as the original joiner."""
        logger.info("Reconnecting as joiner...")
        
        # Set the original offer as remote description (if we stored it)
        if hasattr(self, 'original_remote_offer') and self.original_remote_offer:
            await self.pc.setRemoteDescription(self.original_remote_offer)
        
        # Set our original answer as local description
        await self.pc.setLocalDescription(self.original_answer)
        
        # Wait for ICE gathering with timeout
        try:
            await asyncio.wait_for(self._wait_for_ice_gathering(), timeout=self.connection_timeout)
            logger.info("Reconnection successful (joiner)")
        except asyncio.TimeoutError:
            logger.error("Reconnection timeout (joiner)")
            raise Exception("Reconnection timeout")
    
    async def _start_heartbeat(self) -> None:
        """Start heartbeat mechanism to detect connection issues early."""
        if self.heartbeat_task and not self.heartbeat_task.done():
            return
            
        self.last_heartbeat_response = asyncio.get_event_loop().time()
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def _stop_heartbeat(self) -> None:
        """Stop heartbeat mechanism."""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            self.heartbeat_task = None
    
    async def _heartbeat_loop(self) -> None:
        """Heartbeat loop to monitor connection health."""
        try:
            while self.is_connected:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Send heartbeat message
                if self.channel and self.channel.readyState == "open":
                    heartbeat_msg = json.dumps({
                        "type": "heartbeat",
                        "timestamp": asyncio.get_event_loop().time()
                    })
                    try:
                        self.channel.send(heartbeat_msg)
                        
                        # Check if we've received a response recently
                        current_time = asyncio.get_event_loop().time()
                        if (current_time - self.last_heartbeat_response) > (self.heartbeat_interval * 10):
                            logger.warning("Heartbeat response timeout - connection may be unstable")
                            # Don't trigger reconnection here, let WebRTC state changes handle it
                            
                    except Exception as e:
                        logger.error(f"Failed to send heartbeat: {e}")
                        break
                else:
                    break
                    
        except asyncio.CancelledError:
            logger.debug("Heartbeat loop cancelled")
        except Exception as e:
            logger.error(f"Heartbeat loop error: {e}")
    
    async def _stop_reconnection(self) -> None:
        """Stop any ongoing reconnection attempts."""
        if self.reconnection_task:
            self.reconnection_task.cancel()
            self.reconnection_task = None
    
    def enable_reconnection(self, enabled: bool = True) -> None:
        """Enable or disable automatic reconnection."""
        self.reconnection_enabled = enabled
        logger.info(f"Automatic reconnection {'enabled' if enabled else 'disabled'}")
    
    def set_reconnection_config(self, max_attempts: int = 5, initial_delay: float = 2.0, 
                              max_delay: float = 30.0, connection_timeout: float = 15.0) -> None:
        """Configure reconnection parameters."""
        self.max_reconnection_attempts = max_attempts
        self.reconnection_delay = initial_delay
        self.max_reconnection_delay = max_delay
        self.connection_timeout = connection_timeout
        logger.info(f"Reconnection config: max_attempts={max_attempts}, "
                   f"initial_delay={initial_delay}, max_delay={max_delay}, "
                   f"timeout={connection_timeout}")
    
    def set_heartbeat_config(self, interval: float = 1.0) -> None:
        """Configure heartbeat parameters to prevent inactivity disconnections."""
        self.heartbeat_interval = max(0.5, min(60.0, interval))  # Clamp between 0.5 and 60 seconds
        logger.info(f"Heartbeat interval set to {self.heartbeat_interval} seconds") 
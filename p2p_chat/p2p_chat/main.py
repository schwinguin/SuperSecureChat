"""
Main entry point for the P2P chat application.
Orchestrates the GUI, WebRTC peer, and asyncio event loop integration.
"""

import argparse
import asyncio
import logging
import customtkinter as ctk
import tkinter as tk
from datetime import datetime
import sys
import os
import shutil
from typing import Optional

from .modern_gui import ModernChatWindow
from .rtc_peer import RTCPeer
from .utils import setup_logging, safe_call
from .security import sanitize_message, SecurityViolation, FileSecurityViolation
from .settings_manager import SettingsManager

logger = logging.getLogger(__name__)


class P2PChatApp:
    """
    Main application class that orchestrates GUI and WebRTC peer.
    
    Manages the lifecycle of the application, event handling between
    GUI and WebRTC components, file transfers, and graceful shutdown.
    """
    
    def __init__(self):
        """Initialize the application."""
        self.root = None
        self.window = None
        self.peer = None
        self.loop = None
        self.running = False
        self.peer_username = "Peer"
        # Add cleanup flag to prevent after callbacks from executing
        self.cleanup_started = False
        
        # Settings manager
        self.settings_manager = SettingsManager()
        
    def setup(self) -> None:
        """Set up the application components."""
        # Import here to avoid circular imports
        from p2p_chat.modern_chat_window import ModernChatWindow
        
        logger.info("Starting P2P Chat Application")
        
        # Load settings first
        self.settings_manager.load_settings()
        
        # Initialize the root window
        self.root = ctk.CTk()
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # Initialize the GUI
        self.window = ModernChatWindow(self.root)
        
        # Set audio settings from settings manager
        audio_settings = self.settings_manager.get_audio_settings()
        self.window.set_audio_settings(audio_settings)
        
        # Set up window events
        self.window.on_create_chat = self._wrap_async_callback(self._on_create_chat)
        self.window.on_join_chat = self._wrap_async_callback_with_param(self._on_join_chat)
        self.window.on_connect_chat = self._wrap_async_callback_with_param(self._on_connect_chat)
        self.window.on_send_message = self._on_send_message
        self.window.on_send_file = self._wrap_async_callback_with_param(self._on_send_file)
        self.window.on_accept_file = self._wrap_async_callback_with_dual_param(self._on_accept_file)
        self.window.on_reject_file = self._wrap_async_callback_with_dual_param(self._on_reject_file)
        self.window.on_disconnect_chat = self._wrap_async_callback(self._on_disconnect_chat)
        self.window.on_window_close = self._on_window_close
        
        # Voice chat events
        self.window.on_enable_voice = self._wrap_async_callback(self._on_enable_voice)
        self.window.on_disable_voice = self._wrap_async_callback(self._on_disable_voice)
        self.window.on_start_voice_transmission = self._wrap_async_callback(self._on_start_voice_transmission)
        self.window.on_stop_voice_transmission = self._wrap_async_callback(self._on_stop_voice_transmission)
        self.window.on_audio_settings_changed = self._on_audio_settings_changed
        
        # Create WebRTC peer
        self.peer = RTCPeer()
        
        # Apply audio settings to peer
        self.peer.update_audio_settings(audio_settings)
        
        self._setup_peer_events()
        
        # Configure reconnection settings (can be customized)
        self.configure_reconnection()
        
        logger.info("Application initialized successfully")
    
    def configure_reconnection(self, enabled: bool = True, max_attempts: int = 5, 
                             initial_delay: float = 2.0, max_delay: float = 30.0, 
                             connection_timeout: float = 15.0) -> None:
        """Configure automatic reconnection settings."""
        if self.peer:
            # Get connection settings from settings manager
            if hasattr(self, 'settings_manager'):
                connection_settings = self.settings_manager.get_connection_settings()
                max_attempts = connection_settings.get('max_reconnection_attempts', max_attempts)
                initial_delay = connection_settings.get('initial_reconnection_delay', initial_delay)
                max_delay = connection_settings.get('max_reconnection_delay', max_delay)
                connection_timeout = connection_settings.get('connection_timeout', connection_timeout)
                heartbeat_interval = connection_settings.get('heartbeat_interval', 1.0)
            else:
                heartbeat_interval = 1.0
                
            self.peer.enable_reconnection(enabled)
            self.peer.set_reconnection_config(
                max_attempts=max_attempts,
                initial_delay=initial_delay,
                max_delay=max_delay,
                connection_timeout=connection_timeout
            )
            self.peer.set_heartbeat_config(interval=heartbeat_interval)
            logger.info(f"Reconnection configured: enabled={enabled}, max_attempts={max_attempts}")
            logger.info(f"Heartbeat configured: interval={heartbeat_interval} seconds")
    
    def _wrap_async_callback(self, async_func):
        """Wrap an async function to be callable from GUI thread."""
        def wrapper():
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(async_func())
            except Exception as e:
                logger.error(f"Failed to schedule async callback: {e}")
        return wrapper
    
    def _wrap_async_callback_with_param(self, async_func):
        """Wrap an async function with parameter to be callable from GUI thread."""
        def wrapper(param):
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(async_func(param))
            except Exception as e:
                logger.error(f"Failed to schedule async callback: {e}")
        return wrapper
    
    def _wrap_async_callback_with_dual_param(self, async_func):
        """Wrap an async function with two parameters to be callable from GUI thread."""
        def wrapper(param1, param2):
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(async_func(param1, param2))
            except Exception as e:
                logger.error(f"Failed to schedule async callback: {e}")
        return wrapper
    
    def _setup_peer_events(self) -> None:
        """Set up WebRTC peer event handlers."""
        if not self.peer:
            return
            
        # Connection events
        self.peer.on("connected", self._on_peer_connected)
        self.peer.on("message", self._on_peer_message)
        self.peer.on("error", self._on_peer_error)
        self.peer.on("failed", self._on_peer_failed)
        self.peer.on("closed", self._on_peer_closed)
        self.peer.on("channel_open", self._on_channel_open)
        self.peer.on("channel_close", self._on_channel_close)
        
        # Reconnection events
        self.peer.on("disconnected", self._on_peer_disconnected)
        self.peer.on("reconnection_attempt", self._on_reconnection_attempt)
        self.peer.on("reconnection_failed", self._on_reconnection_failed)
        
        # File transfer events
        self.peer.on("file_offer", self._on_file_offer)
        self.peer.on("file_accepted", self._on_file_accepted)
        self.peer.on("file_rejected", self._on_file_rejected)
        self.peer.on("file_started", self._on_file_started)
        self.peer.on("file_progress", self._on_file_progress)
        self.peer.on("file_send_progress", self._on_file_send_progress)
        self.peer.on("file_completed", self._on_file_completed)
        self.peer.on("file_sent", self._on_file_sent)
        self.peer.on("file_error", self._on_file_error)
        self.peer.on("file_cancelled", self._on_file_cancelled)
        
        # Voice chat events
        self.peer.on("voice_track_received", self._on_voice_track_received)
        if hasattr(self.peer, 'on_voice_state_change'):
            self.peer.on_voice_state_change = self._on_voice_state_change
    
    async def _on_create_chat(self) -> None:
        """Handle create chat request from GUI."""
        try:
            logger.info("Creating new chat...")
            invite_key = await self.peer.create_initiator()
            
            # Schedule GUI update in main thread
            self.root.after(0, lambda: self.window.show_create_panel(invite_key))
            
        except Exception as e:
            error_msg = f"Failed to create chat: {e}"
            logger.error(error_msg)
            self.root.after(0, lambda msg=error_msg: self.window.show_error(msg))
    
    async def _on_join_chat(self, invite_key: str) -> None:
        """Handle join chat request from GUI."""
        try:
            logger.info("Joining chat...")
            return_key = await self.peer.accept_invite(invite_key)
            
            # Schedule GUI update in main thread
            self.root.after(0, lambda: self.window.show_return_key(return_key))
            self.root.after(0, lambda: self.window.set_status("Waiting for connection...", "orange"))
            
        except SecurityViolation as e:
            error_msg = f"Security validation failed: {e}"
            logger.error(error_msg)
            self.root.after(0, lambda msg=error_msg: self.window.show_error(msg))
        except Exception as e:
            error_msg = f"Failed to join chat: {e}"
            logger.error(error_msg)
            self.root.after(0, lambda msg=error_msg: self.window.show_error(msg))
    
    async def _on_connect_chat(self, return_key: str) -> None:
        """Handle connect request from GUI (initiator receiving return key)."""
        try:
            logger.info("Completing handshake...")
            await self.peer.receive_return_key(return_key)
            
        except SecurityViolation as e:
            error_msg = f"Security validation failed: {e}"
            logger.error(error_msg)
            self.root.after(0, lambda msg=error_msg: self.window.show_error(msg))
        except Exception as e:
            error_msg = f"Failed to connect: {e}"
            logger.error(error_msg)
            self.root.after(0, lambda msg=error_msg: self.window.show_error(msg))
    
    def _on_send_message(self, message: str) -> None:
        """Handle send message request from GUI."""
        if not self.peer or not self.peer.is_connected:
            self.window.show_error("Not connected to peer")
            return
        
        try:
            # Get username from GUI
            username = self.window.get_username()
            
            # Create message with username
            message_data = f"{username}|{message}"
            
            # Message sanitization is now handled in RTCPeer.send()
            # Send message with username
            self.peer.send(message_data)
            
            # Add to chat display (sanitize for display as well)
            try:
                sanitized_message = sanitize_message(message)
                timestamp = datetime.now().strftime("%H:%M:%S")
                formatted_message = f"[{timestamp}] {username}: {sanitized_message}"
                self.window.add_message(formatted_message, "sent")
            except SecurityViolation as e:
                # This shouldn't happen since peer.send() already validated
                logger.error(f"Display sanitization failed: {e}")
                self.window.show_error(f"Message display error: {e}")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.window.show_error(f"Failed to send message: {e}")
    
    # File transfer handlers
    
    async def _on_send_file(self, file_path: str) -> None:
        """Handle send file request from GUI."""
        if not self.peer or not self.peer.is_connected:
            self.root.after(0, lambda: self.window.show_error("Not connected to peer"))
            return
        
        try:
            # Initiate file transfer
            transfer_id = self.peer.send_file(file_path)
            
            # Show status message
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%H:%M:%S")
            message = f"[{timestamp}] 📁 Sending file: {filename} (waiting for peer approval...)"
            
            self.root.after(0, lambda: self.window.add_message(message, "system"))
            self.root.after(0, lambda: self.window.set_status(f"File transfer initiated: {filename}", "blue"))
            
        except (FileSecurityViolation, Exception) as e:
            error_msg = f"Failed to send file: {e}"
            logger.error(error_msg)
            self.root.after(0, lambda: self.window.show_error(error_msg))
    
    async def _on_accept_file(self, transfer_id: str, save_path: str) -> None:
        """Handle file acceptance from GUI."""
        try:
            # Create directory if it doesn't exist
            save_dir = os.path.dirname(save_path)
            if save_dir and not os.path.exists(save_dir):
                os.makedirs(save_dir, exist_ok=True)
            
            # Accept the file transfer
            self.peer.accept_file(transfer_id, save_path)
            
            # Show status message
            timestamp = datetime.now().strftime("%H:%M:%S")
            message = f"[{timestamp}] 📁 Accepting file transfer..."
            
            self.root.after(0, lambda: self.window.add_message(message, "system"))
            self.root.after(0, lambda: self.window.set_status("File transfer accepted", "green"))
            
        except Exception as e:
            error_msg = f"Failed to accept file: {e}"
            logger.error(error_msg)
            self.root.after(0, lambda: self.window.show_error(error_msg))
    
    async def _on_reject_file(self, transfer_id: str, reason: str) -> None:
        """Handle file rejection from GUI."""
        try:
            self.peer.reject_file(transfer_id, reason)
            
            # Show status message
            timestamp = datetime.now().strftime("%H:%M:%S")
            message = f"[{timestamp}] ❌ File transfer rejected: {reason}"
            
            self.root.after(0, lambda: self.window.add_message(message, "system"))
            self.root.after(0, lambda: self.window.set_status("File transfer rejected", "red"))
            
        except Exception as e:
            error_msg = f"Failed to reject file: {e}"
            logger.error(error_msg)
            self.root.after(0, lambda: self.window.show_error(error_msg))
    
    # File transfer event handlers
    
    def _on_file_offer(self, offer_data: dict) -> None:
        """Handle incoming file offer from peer."""
        logger.info(f"Received file offer: {offer_data}")
        
        def show_offer():
            self.window.show_file_offer(offer_data)
        
        self.root.after(0, show_offer)
    
    def _on_file_accepted(self, data: dict) -> None:
        """Handle file transfer acceptance notification."""
        transfer_id = data.get('transfer_id')
        logger.info(f"File transfer accepted: {transfer_id}")
        
        def update_gui():
            timestamp = datetime.now().strftime("%H:%M:%S")
            message = f"[{timestamp}] ✅ File transfer accepted by peer - starting upload..."
            self.window.add_message(message, "system")
            self.window.set_status("File transfer starting...", "green")
        
        self._safe_after(0, update_gui)
    
    def _on_file_rejected(self, data: dict) -> None:
        """Handle file transfer rejection notification."""
        transfer_id = data.get('transfer_id')
        reason = data.get('reason', 'No reason provided')
        logger.info(f"File transfer rejected: {transfer_id}, reason: {reason}")
        
        def update_gui():
            timestamp = datetime.now().strftime("%H:%M:%S")
            message = f"[{timestamp}] ❌ File transfer rejected: {reason}"
            self.window.add_message(message, "error")
            self.window.set_status("File transfer rejected", "red")
        
        self._safe_after(0, update_gui)
    
    def _on_file_started(self, data: dict) -> None:
        """Handle file transfer start notification."""
        transfer_id = data.get('transfer_id')
        filename = data.get('filename', 'Unknown')
        logger.info(f"File transfer started: {filename}")
        
        def update_gui():
            # Show progress dialog
            self.window.show_file_progress({
                'transfer_id': transfer_id,
                'filename': filename
            })
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            message = f"[{timestamp}] 📁 File transfer started: {filename}"
            self.window.add_message(message, "system")
            self.window.set_status(f"Receiving: {filename}", "blue")
        
        self._safe_after(0, update_gui)
    
    def _on_file_progress(self, progress_data: dict) -> None:
        """Handle file receive progress updates."""
        def update_gui():
            self.window.update_file_progress(progress_data)
            
            # Update status bar
            filename = progress_data.get('filename', 'file')
            progress = progress_data.get('progress', 0)
            self.window.set_status(f"Receiving {filename}: {progress:.1f}%", "blue")
        
        self._safe_after(0, update_gui)
    
    def _on_file_send_progress(self, progress_data: dict) -> None:
        """Handle file send progress updates."""
        def update_gui():
            self.window.update_file_progress(progress_data)
            
            # Update status bar
            filename = progress_data.get('filename', 'file')
            progress = progress_data.get('progress', 0)
            self.window.set_status(f"Sending {filename}: {progress:.1f}%", "blue")
        
        self._safe_after(0, update_gui)
    
    def _on_file_completed(self, completion_data: dict) -> None:
        """Handle file transfer completion."""
        transfer_id = completion_data.get('transfer_id')
        filename = completion_data.get('filename', 'Unknown')
        temp_path = completion_data.get('temp_path')
        
        logger.info(f"File transfer completed: {filename}")
        
        def update_gui():
            # The temp file needs to be moved to the user's chosen location
            # This will be handled by the GUI layer after user confirmation
            self.window.show_file_completed(completion_data)
            self.window.set_status(f"File received: {filename}", "green")
        
        self._safe_after(0, update_gui)
    
    def _on_file_sent(self, data: dict) -> None:
        """Handle file send completion."""
        transfer_id = data.get('transfer_id')
        filename = data.get('filename', 'Unknown')
        logger.info(f"File sent successfully: {filename}")
        
        def update_gui():
            timestamp = datetime.now().strftime("%H:%M:%S")
            message = f"[{timestamp}] ✅ File sent successfully: {filename}"
            self.window.add_message(message, "system")
            self.window.set_status(f"File sent: {filename}", "green")
        
        self._safe_after(0, update_gui)
    
    def _on_file_error(self, error_data: dict) -> None:
        """Handle file transfer errors."""
        transfer_id = error_data.get('transfer_id')
        error_msg = error_data.get('error', 'Unknown error')
        logger.error(f"File transfer error: {error_msg}")
        
        def update_gui():
            self.window.show_file_error(error_data)
            self.window.set_status(f"File transfer error", "red")
        
        self._safe_after(0, update_gui)
    
    def _on_file_cancelled(self, data: dict) -> None:
        """Handle file transfer cancellation."""
        logger.info(f"File transfer cancelled: {data}")
        
        def update_gui():
            self.window.show_file_error({
                "transfer_id": data.get("transfer_id", "unknown"),
                "error": "Transfer cancelled",
                "filename": data.get("filename", "Unknown file")
            })
        
        self._safe_after(0, update_gui)
    
    def _on_peer_connected(self) -> None:
        """Handle peer connection establishment."""
        logger.info("WebRTC peer connected")
        
        def update_gui():
            self.window.set_status("Connected - waiting for data channel...", "orange")
        
        self._safe_after(0, update_gui)
    
    def _on_peer_message(self, message: str) -> None:
        """Handle incoming message from peer."""
        logger.debug(f"Received message: {message}")
        
        def update_gui():
            try:
                # Parse message to extract username and content
                if "|" in message:
                    peer_username, content = message.split("|", 1)
                    self.peer_username = peer_username.strip() if peer_username.strip() else "Peer"
                else:
                    # Fallback for messages without username
                    content = message
                    peer_username = self.peer_username
                
                # Sanitize received message content for display
                sanitized_message = sanitize_message(content)
                timestamp = datetime.now().strftime("%H:%M:%S")
                formatted_message = f"[{timestamp}] {peer_username}: {sanitized_message}"
                self.window.add_message(formatted_message, "received")
            except SecurityViolation as e:
                logger.warning(f"Received message failed sanitization: {e}")
                timestamp = datetime.now().strftime("%H:%M:%S")
                formatted_message = f"[{timestamp}] System: Received invalid message (filtered for security)"
                self.window.add_message(formatted_message, "system")
            except Exception as e:
                logger.error(f"Error processing received message: {e}")
                timestamp = datetime.now().strftime("%H:%M:%S")
                formatted_message = f"[{timestamp}] System: Error processing message"
                self.window.add_message(formatted_message, "system")
        
        self._safe_after(0, update_gui)
    
    def _on_peer_error(self, error: str) -> None:
        """Handle peer errors."""
        logger.error(f"Peer error: {error}")
        self._safe_after(0, lambda: self.window.show_error(error))
    
    def _on_peer_failed(self, error: str) -> None:
        """Handle peer connection failure."""
        logger.error(f"Peer connection failed: {error}")
        
        def update_gui():
            self.window.set_status("Connection Failed", "red")
            self.window.show_error(f"Connection failed: {error}")
        
        self._safe_after(0, update_gui)
    
    def _on_peer_closed(self) -> None:
        """Handle peer connection closure."""
        logger.info("Peer connection closed")
        
        def update_gui():
            self.window.set_status("Disconnected", "red")
            if hasattr(self.window, 'chat_display') and self.window.chat_display:
                self.window.add_message("=== Disconnected from peer ===", "system")
        
        self._safe_after(0, update_gui)
    
    def _on_peer_disconnected(self) -> None:
        """Handle peer disconnection with potential for reconnection."""
        logger.info("Peer disconnected - attempting reconnection...")
        
        def update_gui():
            self.window.set_status("Disconnected - Reconnecting...", "orange")
            if hasattr(self.window, 'chat_display') and self.window.chat_display:
                self.window.add_message("=== Connection lost - attempting to reconnect ===", "system")
        
        self._safe_after(0, update_gui)
    
    def _on_reconnection_attempt(self, attempt_number: int) -> None:
        """Handle reconnection attempt notification."""
        logger.info(f"Reconnection attempt {attempt_number}")
        
        def update_gui():
            self.window.set_status(f"Reconnecting... (attempt {attempt_number})", "orange")
        
        self._safe_after(0, update_gui)
    
    def _on_reconnection_failed(self, error_message: str) -> None:
        """Handle reconnection failure."""
        logger.error(f"Reconnection failed: {error_message}")
        
        def update_gui():
            self.window.set_status("Reconnection Failed", "red")
            self.window.show_error(f"Failed to reconnect: {error_message}")
        
        self._safe_after(0, update_gui)
    
    def _on_channel_open(self) -> None:
        """Handle data channel opening."""
        logger.info("Data channel opened - transitioning to chat")
        
        def update_gui():
            self.window.show_chat()
            self.window.add_message("=== Connected to peer ===", "system")
            self.window.add_message("🔒 Your communication is end-to-end encrypted!", "system")
            self.window.set_status("Ready to chat", "green")
        
        self._safe_after(0, update_gui)
    
    def _on_channel_close(self) -> None:
        """Handle data channel closure."""
        logger.info("Data channel closed")
        
        def update_gui():
            self.window.set_status("Channel Closed", "orange")
        
        self._safe_after(0, update_gui)
    
    def _on_window_close(self) -> None:
        """Handle window close event."""
        logger.info("Window closing...")
        # Set cleanup flag to prevent new after callbacks
        self.cleanup_started = True
        self.running = False
        
        # Close peer connection first
        if self.peer:
            asyncio.create_task(self.peer.close())
        
        # Wait a brief moment for any pending callbacks to complete
        try:
            if self.root:
                self.root.after(50, self._destroy_window)
        except Exception:
            # If we can't schedule the delayed destroy, destroy immediately
            self._destroy_window()
    
    def _destroy_window(self) -> None:
        """Destroy the window safely."""
        try:
            if self.root:
                # Try to clean up CustomTkinter's internal trackers
                try:
                    # Disable CustomTkinter's update loops
                    import customtkinter.windows.widgets.scaling.scaling_tracker as scaling_tracker
                    import customtkinter.windows.widgets.appearance_mode.appearance_mode_tracker as appearance_tracker
                    
                    # Stop the update loops
                    scaling_tracker.ScalingTracker.update_loop_running = False
                    appearance_tracker.AppearanceModeTracker.update_loop_running = False
                    
                    # Clear tracking dictionaries
                    if self.root in scaling_tracker.ScalingTracker.window_widgets_dict:
                        del scaling_tracker.ScalingTracker.window_widgets_dict[self.root]
                    if self.root in scaling_tracker.ScalingTracker.window_dpi_scaling_dict:
                        del scaling_tracker.ScalingTracker.window_dpi_scaling_dict[self.root]
                    
                    # Remove from appearance tracker
                    if self.root in appearance_tracker.AppearanceModeTracker.app_list:
                        appearance_tracker.AppearanceModeTracker.app_list.remove(self.root)
                        
                except Exception as e:
                    logger.debug(f"Could not clean up CustomTkinter trackers: {e}")
                
                self.root.quit()  # Exit the mainloop
                self.root.destroy()
        except Exception as e:
            logger.debug(f"Exception during window destruction: {e}")
    
    async def async_mainloop(self) -> None:
        """Run the asyncio event loop integrated with Tkinter."""
        self.running = True
        
        while self.running:
            try:
                # Update Tkinter
                if self.root and not self.cleanup_started:
                    self.root.update()
                
                # Allow other coroutines to run
                await asyncio.sleep(0.01)
                
            except tk.TclError as e:
                # Window was closed or destroyed
                logger.debug(f"TclError in main loop: {e}")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                break
        
        logger.info("Main loop exited")
    
    async def run_async(self) -> None:
        """Run the application asynchronously."""
        try:
            await self.async_mainloop()
        finally:
            await self.cleanup()
    
    async def cleanup(self) -> None:
        """Clean up application resources."""
        logger.info("Cleaning up application...")
        
        if self.peer:
            # Disable reconnection during cleanup
            self.peer.enable_reconnection(False)
            await self.peer.close()
        
        logger.info("Cleanup completed")
    
    def run(self) -> None:
        """Run the application."""
        self.setup()
        
        try:
            # Run the asyncio event loop
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            logger.info("Application shutting down")

    # Voice Chat Event Handlers
    
    async def _on_enable_voice(self) -> None:
        """Handle voice chat enable request from GUI."""
        try:
            logger.info("Enabling voice chat...")
            await self.peer.enable_voice_chat()
            
            # Update GUI status
            self._safe_after(0, lambda: self.window.update_voice_status("Enabled"))
            
        except Exception as e:
            error_msg = f"Failed to enable voice chat: {e}"
            logger.error(error_msg)
            self._safe_after(0, lambda: self.window.show_error(error_msg))
            self._safe_after(0, lambda: self.window.set_voice_enabled(False))
    
    async def _on_disable_voice(self) -> None:
        """Handle voice chat disable request from GUI."""
        try:
            logger.info("Disabling voice chat...")
            await self.peer.disable_voice_chat()
            
            # Update GUI status
            self._safe_after(0, lambda: self.window.update_voice_status("Disabled"))
            
        except Exception as e:
            error_msg = f"Failed to disable voice chat: {e}"
            logger.error(error_msg)
            self._safe_after(0, lambda: self.window.show_error(error_msg))
    
    async def _on_start_voice_transmission(self) -> None:
        """Handle start voice transmission request from GUI."""
        try:
            await self.peer.start_voice_transmission()
        except Exception as e:
            logger.error(f"Failed to start voice transmission: {e}")
            self._safe_after(0, lambda: self.window.show_error(f"Voice transmission error: {e}"))
    
    async def _on_stop_voice_transmission(self) -> None:
        """Handle stop voice transmission request from GUI."""
        try:
            await self.peer.stop_voice_transmission()
        except Exception as e:
            logger.error(f"Failed to stop voice transmission: {e}")
    
    def _on_voice_track_received(self, track) -> None:
        """Handle voice track received from peer."""
        logger.info("Voice track received from peer")
        
        def update_gui():
            self.window.add_message(f"🔊 Voice connection established with {self.peer_username}", "voice")
        
        self._safe_after(0, update_gui)
    
    async def _on_voice_state_change(self, state: str, error_msg: str = None) -> None:
        """Handle voice state changes."""
        logger.info(f"Voice state changed: {state}")
        
        def update_gui():
            if state == "enabled":
                self.window.set_voice_enabled(True)
                self.window.update_voice_status("Voice Chat: Enabled")
            elif state == "disabled":
                self.window.set_voice_enabled(False)
                self.window.update_voice_status("Voice Chat: Disabled")
            elif state == "transmitting":
                self.window.update_voice_status("Voice Chat: Transmitting")
            elif state == "listening":
                self.window.update_voice_status("Voice Chat: Listening")
            elif state == "error":
                self.window.set_voice_enabled(False)
                self.window.update_voice_status(f"Voice Chat: Error")
                if error_msg:
                    self.window.show_error(f"Voice chat error: {error_msg}")
        
        self._safe_after(0, update_gui)
    
    def _on_audio_settings_changed(self, settings: dict) -> None:
        """Handle audio settings changed from GUI."""
        logger.info(f"Audio settings changed: {settings}")
        
        # Update settings in peer
        if self.peer:
            self.peer.update_audio_settings(settings)
        
        # Save settings to file
        self.settings_manager.update_audio_settings(settings)

    def _safe_after(self, delay, callback):
        """Safely schedule a callback, checking if cleanup has started."""
        if not self.cleanup_started and self.root:
            try:
                self.root.after(delay, callback)
            except (tk.TclError, RuntimeError) as e:
                # Widget has been destroyed or application is shutting down
                logger.debug(f"Cannot schedule after callback: {e}")
            except Exception as e:
                # Any other exception during scheduling
                logger.debug(f"Unexpected error scheduling callback: {e}")

    async def _on_disconnect_chat(self) -> None:
        """Handle disconnect request from GUI."""
        try:
            logger.info("Disconnecting from chat...")
            
            if self.peer and self.peer.is_connected:
                # Send a disconnect message to peer before closing
                try:
                    self.peer.send_message("__DISCONNECT__")
                    await asyncio.sleep(0.1)  # Brief delay to allow message to send
                except Exception as e:
                    logger.warning(f"Failed to send disconnect message: {e}")
                
                # Close the peer connection
                await self.peer.close()
            
            # Update GUI in main thread
            def update_gui():
                self.window.set_status("Disconnected", "gray")
                self.window.add_message("=== Disconnected from chat ===", "system")
            
            self._safe_after(0, update_gui)
            
        except Exception as e:
            error_msg = f"Error during disconnect: {e}"
            logger.error(error_msg)
            self._safe_after(0, lambda msg=error_msg: self.window.show_error(msg))


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="P2P Secure Chat Application")
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        setup_logging(logging.DEBUG)
    else:
        setup_logging(logging.INFO)
    
    # Create and run application
    app = P2PChatApp()
    app.run()


if __name__ == "__main__":
    main() 
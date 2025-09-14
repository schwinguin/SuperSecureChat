"""
File Progress Dialog for the P2P chat application.
Handles file transfer progress display with modern UI.
"""

import customtkinter as ctk
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class FileProgressDialog(ctk.CTkToplevel):
    """Dialog for showing file transfer progress."""
    
    def __init__(self, parent, transfer_info: Dict[str, Any], on_cancel: callable = None):
        super().__init__(parent)
        
        self.transfer_info = transfer_info
        self.on_cancel = on_cancel
        
        self.title("File Transfer Progress")
        self.geometry("450x250")
        self.resizable(False, False)
        
        # Make dialog transient but not modal to avoid blocking
        self.transient(parent)
        
        # Keep dialog on top but don't make it modal
        self.attributes("-topmost", True)
        
        # Handle window close (X button) and other close events
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)
        self.bind("<Escape>", lambda e: self._on_window_close())
        
        self._setup_ui()
        
        # Center on parent and ensure visibility
        self.after(100, self._center_on_parent)
        self.after(200, self._ensure_visible)
    
    
    def _ensure_visible(self):
        """Ensure the dialog is visible and on top."""
        try:
            self.lift()
            self.focus_force()
        except Exception as e:
            logger.warning(f"Could not ensure dialog visibility: {e}")
        
    def _setup_ui(self):
        """Set up the progress dialog UI."""
        # Main frame
        main_frame = ctk.CTkFrame(self, corner_radius=0)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="📁 File Transfer in Progress",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(20, 15))
        
        # File info
        filename = self.transfer_info.get('filename', 'Unknown')
        info_label = ctk.CTkLabel(
            main_frame,
            text=f"Transferring: {filename}",
            font=ctk.CTkFont(size=14)
        )
        info_label.pack(pady=5)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(main_frame, width=350, height=20)
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)
        
        # Progress label
        self.progress_label = ctk.CTkLabel(
            main_frame,
            text="0% - Starting transfer...",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(pady=5)
        
        # Cancel button
        self.cancel_btn = ctk.CTkButton(
            main_frame,
            text="Cancel",
            width=100,
            height=35,
            fg_color=("gray40", "gray40"),
            hover_color=("gray50", "gray30"),
            corner_radius=8,
            command=self._on_cancel_click
        )
        self.cancel_btn.pack(pady=(15, 20))
    
    def update_progress(self, progress_data: Dict[str, Any]):
        """Update the progress display."""
        progress = progress_data.get('progress', 0)
        bytes_transferred = progress_data.get('bytes_transferred', 0)
        total_bytes = progress_data.get('total_bytes', 0)
        
        # Update progress bar
        self.progress_bar.set(progress / 100.0)
        
        # Update progress label
        if total_bytes > 0:
            mb_transferred = bytes_transferred / (1024 * 1024)
            mb_total = total_bytes / (1024 * 1024)
            self.progress_label.configure(
                text=f"{progress:.1f}% - {mb_transferred:.2f} MB / {mb_total:.2f} MB"
            )
        else:
            self.progress_label.configure(text=f"{progress:.1f}%")
    
    def _center_on_parent(self):
        """Center dialog on parent window."""
        self.update_idletasks()
        
        try:
            # Get parent geometry
            parent_x = self.master.winfo_x()
            parent_y = self.master.winfo_y()
            parent_width = self.master.winfo_width()
            parent_height = self.master.winfo_height()
            
            # Calculate center position
            x = parent_x + (parent_width - self.winfo_width()) // 2
            y = parent_y + (parent_height - self.winfo_height()) // 2
            
            self.geometry(f"+{x}+{y}")
        except Exception as e:
            logger.warning(f"Could not center progress dialog: {e}")
            self.geometry("+350+250")
    
    def _on_cancel_click(self):
        """Handle cancel button click."""
        logger.info("Cancel button clicked - cancelling file transfer")
        if self.on_cancel:
            transfer_id = self.transfer_info.get('transfer_id')
            if transfer_id:
                self.on_cancel(transfer_id)
        self._cleanup_and_destroy()
    
    def _on_window_close(self):
        """Handle window close (X button) - cancel transfer and close dialog."""
        logger.info("File progress dialog closed by user (X button) - cancelling transfer")
        if self.on_cancel:
            transfer_id = self.transfer_info.get('transfer_id')
            if transfer_id:
                self.on_cancel(transfer_id)
        self._cleanup_and_destroy()
    
    def _cleanup_and_destroy(self):
        """Clean up dialog resources and destroy the window."""
        try:
            # Remove topmost attribute if set
            self.attributes("-topmost", False)
        except Exception as e:
            logger.debug(f"Could not remove topmost attribute: {e}")
        
        # Destroy the window
        self.destroy()
        logger.debug("File progress dialog destroyed") 
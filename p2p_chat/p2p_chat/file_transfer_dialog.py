"""
File Transfer Dialog for the P2P chat application.
Handles file transfer offer dialogs with modern UI.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import logging
import os
from typing import Callable, Dict, Any

logger = logging.getLogger(__name__)


class FileTransferDialog(ctk.CTkToplevel):
    """Dialog for handling file transfer offers and progress."""
    
    def __init__(self, parent, offer_data: Dict[str, Any], on_accept: Callable, on_reject: Callable):
        super().__init__(parent)
        
        self.offer_data = offer_data
        self.on_accept = on_accept
        self.on_reject = on_reject
        
        self.title("File Transfer Offer")
        self.geometry("500x350")
        self.resizable(False, False)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Debug logging
        filename = offer_data.get('filename', 'Unknown')
        file_size = offer_data.get('file_size', 0)
        logger.info(f"Creating file transfer dialog for: {filename} ({file_size} bytes)")
        
        self._setup_ui()
        
        # Center on parent and bring to front
        self.after(100, self._center_on_parent)
        self.lift()
        self.focus_force()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        logger.info("Setting up file transfer dialog UI...")
        
        # Main frame with better padding
        main_frame = ctk.CTkFrame(self, corner_radius=15)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Icon and title
        title_label = ctk.CTkLabel(
            main_frame,
            text="📁 Incoming File Transfer",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # File info frame
        info_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=10)
        
        # File details
        filename = self.offer_data.get('filename', 'Unknown')
        file_size = self.offer_data.get('file_size', 0)
        size_mb = file_size / (1024 * 1024) if file_size > 0 else 0
        
        filename_label = ctk.CTkLabel(
            info_frame,
            text=f"📄 Filename: {filename}",
            font=ctk.CTkFont(size=14)
        )
        filename_label.pack(pady=(15, 5), padx=20, anchor="w")
        
        size_label = ctk.CTkLabel(
            info_frame,
            text=f"📏 Size: {size_mb:.2f} MB ({file_size:,} bytes)",
            font=ctk.CTkFont(size=14)
        )
        size_label.pack(pady=5, padx=20, anchor="w")
        
        # Buttons frame with explicit configuration
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(15, 20))
        
        # Configure button frame grid
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # Accept button
        self.accept_btn = ctk.CTkButton(
            button_frame,
            text="✅ Accept",
            width=140,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("gray50", "gray30"),
            hover_color=("gray60", "gray20"),
            command=self._on_accept_click
        )
        self.accept_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        # Reject button
        self.reject_btn = ctk.CTkButton(
            button_frame,
            text="❌ Reject",
            width=140,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("gray40", "gray40"),
            hover_color=("gray50", "gray30"),
            command=self._on_reject_click
        )
        self.reject_btn.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        
        # Focus on reject button by default (safer)
        self.reject_btn.focus()
        
        logger.info("File transfer dialog UI setup complete - buttons should be visible")
    
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
            logger.info(f"File transfer dialog centered at ({x}, {y})")
        except Exception as e:
            logger.warning(f"Could not center dialog: {e}")
            # Fallback to center of screen
            self.geometry("+300+200")
    
    def _on_accept_click(self):
        """Handle accept button click."""
        logger.info("Accept button clicked - opening file save dialog")
        
        try:
            # Ask user where to save the file
            filename = self.offer_data.get('filename', 'download')
            initial_dir = os.path.expanduser("~/Downloads")
            
            save_path = filedialog.asksaveasfilename(
                title="Save File As",
                initialdir=initial_dir,
                initialfile=filename,
                defaultextension=os.path.splitext(filename)[1] if '.' in filename else '',
                filetypes=[
                    ("All Files", "*.*"),
                    ("Text Files", "*.txt"),
                    ("Images", "*.png *.jpg *.jpeg *.gif *.bmp"),
                    ("Documents", "*.pdf *.doc *.docx"),
                    ("Archives", "*.zip *.rar *.7z")
                ]
            )
            
            if save_path:
                logger.info(f"User selected save path: {save_path}")
                self.on_accept(self.offer_data['transfer_id'], save_path)
                self.destroy()
            else:
                logger.info("User cancelled file save dialog")
        except Exception as e:
            logger.error(f"Error in accept button handler: {e}")
            messagebox.showerror("Error", f"Failed to save file: {e}")
    
    def _on_reject_click(self):
        """Handle reject button click."""
        logger.info("Reject button clicked")
        self.on_reject(self.offer_data['transfer_id'], "User declined")
        self.destroy() 
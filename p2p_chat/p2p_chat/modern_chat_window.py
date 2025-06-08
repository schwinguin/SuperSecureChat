"""
Modern Chat Window for the P2P chat application.
Main UI class that provides the modern interface with dark/light theme support.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import logging
import os
import shutil
from datetime import datetime
from typing import Callable, Optional, Dict, Any

from .file_transfer_dialog import FileTransferDialog
from .file_progress_dialog import FileProgressDialog
from .audio_settings_dialog import AudioSettingsDialog

logger = logging.getLogger(__name__)


class ModernChatWindow:
    """
    Ultra-Modern GUI window for the P2P chat application.
    
    Features sleek design, dark/light themes, modern UI elements, and file transfer capabilities.
    Manages different panels for chat creation, joining, and messaging.
    """
    
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("🔒 P2P Secure Chat")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)
        
        # Configure window
        self.root.iconbitmap("")  # You can add an icon file here
        
        # Callbacks - to be set by main.py
        self.on_create_chat: Optional[Callable] = None
        self.on_join_chat: Optional[Callable] = None
        self.on_connect_chat: Optional[Callable] = None
        self.on_send_message: Optional[Callable] = None
        self.on_send_file: Optional[Callable] = None
        self.on_accept_file: Optional[Callable] = None
        self.on_reject_file: Optional[Callable] = None
        self.on_disconnect_chat: Optional[Callable] = None  # Add disconnect callback
        
        # Voice chat callbacks
        self.on_enable_voice: Optional[Callable] = None
        self.on_disable_voice: Optional[Callable] = None
        self.on_start_voice_transmission: Optional[Callable] = None
        self.on_stop_voice_transmission: Optional[Callable] = None
        
        # Audio settings callback
        self.on_audio_settings_changed: Optional[Callable] = None
        
        # Audio settings storage
        self.current_audio_settings: Dict[str, Any] = {}
        
        # UI state
        self.current_panel = None
        self.invite_key = ""
        self.return_key = ""
        self.stored_username = "Anonymous"
        
        # Voice chat state
        self.voice_enabled = False
        self.voice_transmitting = False
        
        # File transfer tracking
        self.active_progress_dialogs: Dict[str, FileProgressDialog] = {}
        
        self._setup_ui()
        self._show_start_panel()
    
    def _setup_ui(self) -> None:
        """Set up the main UI structure with simplified design."""
        # Configure grid weights
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Single main container - removed unnecessary main_frame wrapper
        self.panel_frame = ctk.CTkFrame(self.root, corner_radius=15)
        self.panel_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.panel_frame.grid_columnconfigure(0, weight=1)
        self.panel_frame.grid_rowconfigure(1, weight=1)
        
        # Simple title without extra frame wrapper
        title_label = ctk.CTkLabel(
            self.panel_frame,
            text="🔒 P2P Secure Chat",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, pady=(20, 10))
        
        # Content area - removed panel_frame wrapper
        self.content_frame = ctk.CTkFrame(self.panel_frame, corner_radius=10, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Simplified status bar
        status_frame = ctk.CTkFrame(self.panel_frame, height=40, corner_radius=8)
        status_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray50")
        )
        self.status_label.grid(row=0, column=0, pady=8)
        
        # Audio settings button
        self.audio_settings_button = ctk.CTkButton(
            status_frame,
            text="🎵",
            width=40,
            height=30,
            command=self._show_audio_settings,
            font=ctk.CTkFont(size=16)
        )
        self.audio_settings_button.grid(row=0, column=1, padx=(0, 5), pady=5, sticky="e")
        
        # Theme toggle button
        self.theme_button = ctk.CTkButton(
            status_frame,
            text="🌙",
            width=40,
            height=30,
            command=self._toggle_theme,
            font=ctk.CTkFont(size=16)
        )
        self.theme_button.grid(row=0, column=2, padx=(0, 10), pady=5, sticky="e")
    
    def _toggle_theme(self):
        """Toggle between dark and light themes."""
        current = ctk.get_appearance_mode()
        new_mode = "light" if current == "Dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        
        # Update theme button emoji
        self.theme_button.configure(text="☀️" if new_mode == "dark" else "🌙")
    
    def _show_audio_settings(self):
        """Show the audio settings dialog."""
        try:
            dialog = AudioSettingsDialog(self.root, self.current_audio_settings)
            dialog.on_settings_saved = self._on_audio_settings_saved
            dialog.show()
        except Exception as e:
            logger.error(f"Failed to show audio settings: {e}")
            messagebox.showerror("Error", f"Failed to open audio settings:\n{e}")
    
    def _on_audio_settings_saved(self, settings: Dict[str, Any]):
        """Handle audio settings being saved."""
        self.current_audio_settings = settings
        logger.info(f"Audio settings updated in GUI: {settings}")
        
        # Call the callback if set
        if self.on_audio_settings_changed:
            self.on_audio_settings_changed(settings)
            
        # Show confirmation
        device_info = []
        if 'input_device_name' in settings:
            device_info.append(f"Input: {settings['input_device_name']}")
        if 'output_device_name' in settings:
            device_info.append(f"Output: {settings['output_device_name']}")
        if 'sample_rate' in settings:
            device_info.append(f"Quality: {settings['sample_rate']} Hz")
            
        device_text = " • ".join(device_info) if device_info else "Default devices"
        self.set_status(f"Audio settings saved: {device_text}", "blue")
    
    def set_audio_settings(self, settings: Dict[str, Any]):
        """Set the current audio settings from external source."""
        self.current_audio_settings = settings
    
    def _show_start_panel(self) -> None:
        """Show the simplified start panel with Create/Join buttons."""
        self._clear_panel()
        
        # Single content panel without extra wrappers
        panel = ctk.CTkFrame(self.content_frame, corner_radius=10)
        panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        panel.grid_columnconfigure(0, weight=1)
        
        # Direct welcome section without wrapper frame
        welcome_label = ctk.CTkLabel(
            panel,
            text="Welcome to Secure P2P Chat",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        welcome_label.grid(row=0, column=0, pady=(30, 5))
        
        subtitle_label = ctk.CTkLabel(
            panel,
            text="End-to-end encrypted • Direct peer connection • No servers",
            font=ctk.CTkFont(size=14),
            text_color=("gray40", "gray60")
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 30))
        
        # Username input without wrapper frame
        username_label = ctk.CTkLabel(
            panel,
            text="👤 Your Name:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        username_label.grid(row=2, column=0, pady=(0, 10))
        
        self.username_entry = ctk.CTkEntry(
            panel,
            placeholder_text="Enter your chat name (optional)",
            font=ctk.CTkFont(size=14),
            height=40,
            corner_radius=8,
            width=400
        )
        self.username_entry.grid(row=3, column=0, pady=(0, 30))
        
        # Action buttons without wrapper frame
        self.create_btn = ctk.CTkButton(
            panel,
            text="🚀 Create Chat",
            width=200,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=12,
            command=self._on_create_chat,
            hover_color=("gray20", "gray80")
        )
        self.create_btn.grid(row=4, column=0, pady=(0, 15))
        
        self.join_btn = ctk.CTkButton(
            panel,
            text="🔗 Join Chat",
            width=200,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=12,
            command=self._on_join_chat,
            fg_color=("gray60", "gray30"),
            hover_color=("gray50", "gray40")
        )
        self.join_btn.grid(row=5, column=0, pady=(0, 30))
        
        self.current_panel = panel
    
    def _show_create_panel(self) -> None:
        """Show the simplified create chat panel."""
        print("🎯 Creating create panel...")
        self._clear_panel()
        
        # Single scrollable panel
        panel = ctk.CTkScrollableFrame(self.content_frame, corner_radius=10)
        panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        panel.grid_columnconfigure(0, weight=1)
        
        # Direct instruction section
        ctk.CTkLabel(
            panel,
            text="🎯 Creating Secure Chat Room",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("gray10", "gray90")
        ).grid(row=0, column=0, pady=(20, 5))
        
        ctk.CTkLabel(
            panel,
            text="1. Share your invite key  •  2. Wait for their return key  •  3. Paste it below to connect",
            font=ctk.CTkFont(size=14),
            text_color=("gray40", "gray60")
        ).grid(row=1, column=0, pady=(0, 20))
        
        # Invite key section
        ctk.CTkLabel(
            panel,
            text="📤 Your Invite Key (Share This)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray30", "gray70")  # Use gray shades instead of blue
        ).grid(row=2, column=0, pady=(0, 10))
        
        self.invite_text = ctk.CTkTextbox(
            panel,
            height=100,
            font=ctk.CTkFont(size=12, family="monospace"),
            corner_radius=8,
            state="normal"
        )
        self.invite_text.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))
        
        self.copy_invite_btn = ctk.CTkButton(
            panel,
            text="📋 Copy to Clipboard",
            height=35,
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            command=self._copy_invite_key,
            fg_color=("gray45", "gray35"),  # Background shade instead of green
            hover_color=("gray55", "gray25")
        )
        self.copy_invite_btn.grid(row=4, column=0, pady=(0, 20))
        
        # Return key section
        ctk.CTkLabel(
            panel,
            text="📥 Return Key (Paste Here)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray30", "gray70")  # Use gray shades instead of gold
        ).grid(row=5, column=0, pady=(0, 10))
        
        self.return_entry = ctk.CTkTextbox(
            panel,
            height=100,
            font=ctk.CTkFont(size=12, family="monospace"),
            corner_radius=8
        )
        self.return_entry.grid(row=6, column=0, sticky="ew", padx=20, pady=(0, 10))
        self.return_entry.insert("0.0", "Paste the return key from your peer here...")
        
        self.connect_btn = ctk.CTkButton(
            panel,
            text="🔗 Connect Now",
            height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=8,
            command=self._on_connect,
            fg_color=("gray50", "gray30"),  # Background shade instead of purple
            hover_color=("gray60", "gray20")
        )
        self.connect_btn.grid(row=7, column=0, pady=(0, 20))
        
        # Back button
        ctk.CTkButton(
            panel,
            text="← Back to Start",
            width=150,
            height=35,
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            command=self._show_start_panel,
            fg_color=("gray60", "gray40"),
            hover_color=("gray50", "gray50")
        ).grid(row=8, column=0, pady=(0, 20))
        
        self.current_panel = panel
        print("✅ Create panel setup complete")
    
    def _show_join_panel(self) -> None:
        """Show the simplified join chat panel."""
        print("🔗 Creating join panel...")
        self._clear_panel()
        
        # Single panel without wrapper frames
        panel = ctk.CTkFrame(self.content_frame, corner_radius=10)
        panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        panel.grid_columnconfigure(0, weight=1)
        
        # Direct instruction section
        ctk.CTkLabel(
            panel,
            text="🔗 Join Existing Chat",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("gray10", "gray90")
        ).grid(row=0, column=0, pady=(30, 5))
        
        ctk.CTkLabel(
            panel,
            text="Paste the invite key you received from your peer below",
            font=ctk.CTkFont(size=14),
            text_color=("gray40", "gray60")
        ).grid(row=1, column=0, pady=(0, 30))
        
        # Invite key input section
        ctk.CTkLabel(
            panel,
            text="📨 Invite Key",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray30", "gray70")  # Use gray shades instead of blue
        ).grid(row=2, column=0, pady=(0, 10))
        
        self.join_entry = ctk.CTkTextbox(
            panel,
            height=120,
            font=ctk.CTkFont(size=12, family="monospace"),
            corner_radius=8
        )
        self.join_entry.grid(row=3, column=0, sticky="ew", padx=30, pady=(0, 10))
        self.join_entry.insert("0.0", "Paste the invite key here...")
        
        self.join_submit_btn = ctk.CTkButton(
            panel,
            text="🚀 Join Chat",
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=10,
            command=self._on_join_with_key,
            fg_color=("gray50", "gray30"),  # Background shade instead of gold
            hover_color=("gray60", "gray20")
        )
        self.join_submit_btn.grid(row=4, column=0, pady=(0, 30))
        
        # Return key display section (initially hidden)
        self.return_display_frame = ctk.CTkFrame(panel, corner_radius=8)
        self.return_display_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            self.return_display_frame,
            text="📤 Your Return Key (Share This Back)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray30", "gray70")  # Use gray shades instead of green
        ).grid(row=0, column=0, pady=(15, 10))
        
        self.return_display_text = ctk.CTkTextbox(
            self.return_display_frame,
            height=100,
            font=ctk.CTkFont(size=12, family="monospace"),
            corner_radius=8,
            state="disabled"
        )
        self.return_display_text.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))
        
        self.copy_return_btn = ctk.CTkButton(
            self.return_display_frame,
            text="📋 Copy Return Key",
            height=35,
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            command=self._copy_return_key,
            fg_color=("gray45", "gray35"),  # Background shade instead of green
            hover_color=("gray55", "gray25")
        )
        self.copy_return_btn.grid(row=2, column=0, pady=(0, 15))
        
        # Back button
        ctk.CTkButton(
            panel,
            text="← Back to Start",
            width=150,
            height=35,
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            command=self._show_start_panel,
            fg_color=("gray60", "gray40"),
            hover_color=("gray50", "gray50")
        ).grid(row=6, column=0, pady=30)
        
        self.current_panel = panel
        print("✅ Join panel setup complete")
    
    def _show_chat_panel(self) -> None:
        """Show the enhanced chat interface with file transfer and voice chat capabilities."""
        self._clear_panel()
        
        # Single panel for chat
        panel = ctk.CTkFrame(self.content_frame, corner_radius=10)
        panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(0, weight=1)
        
        # Chat display area
        self.chat_display = ctk.CTkTextbox(
            panel,
            corner_radius=8,
            font=ctk.CTkFont(size=16),  # Keep larger font for readability
            state="disabled",
            wrap="word"
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=15, pady=15, columnspan=2)

        # Input and controls frame (compact)
        input_frame = ctk.CTkFrame(panel, fg_color="transparent")
        input_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15), columnspan=2)
        input_frame.grid_columnconfigure(0, weight=1)

        # Message input (smaller)
        self.message_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type your message here... (Press Enter to send)",
            font=ctk.CTkFont(size=14),
            height=35,  # Reduced from 45
            corner_radius=8
        )
        self.message_entry.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.message_entry.bind("<Return>", self._on_send)

        # Compact action buttons row
        button_row = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_row.grid(row=1, column=0, sticky="ew")
        button_row.grid_columnconfigure(0, weight=1)
        button_row.grid_columnconfigure(1, weight=0)
        button_row.grid_columnconfigure(2, weight=0)
        button_row.grid_columnconfigure(3, weight=0)
        button_row.grid_columnconfigure(4, weight=0)

        # Send message button (compact)
        self.send_btn = ctk.CTkButton(
            button_row,
            text="📤 Send",
            width=80,
            height=32,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=6,
            command=self._on_send,
            fg_color=("gray50", "gray30"),
            hover_color=("gray60", "gray20")
        )
        self.send_btn.grid(row=0, column=0, padx=(0, 5), sticky="w")

        # Send file button (compact)
        self.file_btn = ctk.CTkButton(
            button_row,
            text="📁 File",
            width=70,
            height=32,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=6,
            command=self._on_send_file,
            fg_color=("gray45", "gray35"),
            hover_color=("gray55", "gray25")
        )
        self.file_btn.grid(row=0, column=1, padx=5, sticky="w")

        # Voice enable button (compact)
        self.voice_enable_btn = ctk.CTkButton(
            button_row,
            text="🎤 Voice",
            width=80,
            height=32,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=6,
            command=self._on_voice_enable_toggle,
            fg_color=("gray60", "gray40"),
            hover_color=("gray50", "gray50")
        )
        self.voice_enable_btn.grid(row=0, column=2, padx=5, sticky="w")

        # Push-to-talk button (compact, initially hidden)
        self.voice_ptt_btn = ctk.CTkButton(
            button_row,
            text="🗣️ Talk",
            width=70,
            height=32,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=6,
            state="disabled",
            fg_color=("gray40", "gray40"),
            hover_color=("gray50", "gray30")
        )
        self.voice_ptt_btn.grid(row=0, column=3, padx=5, sticky="w")

        # Bind mouse events for push-to-talk
        self.voice_ptt_btn.bind("<Button-1>", self._on_voice_start)
        self.voice_ptt_btn.bind("<ButtonRelease-1>", self._on_voice_stop)

        # Disconnect button (compact, right side)
        self.disconnect_btn = ctk.CTkButton(
            button_row,
            text="🚪 Leave",
            width=70,
            height=32,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=6,
            command=self._on_disconnect,
            fg_color=("gray40", "gray40"),
            hover_color=("gray50", "gray30")
        )
        self.disconnect_btn.grid(row=0, column=4, sticky="e")

        # Compact status/voice info (optional, only when voice is active)
        self.voice_status_label = ctk.CTkLabel(
            input_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
            height=0  # Minimal height
        )
        # Initially hidden

        self.current_panel = panel
        
        # Focus on message entry
        self.message_entry.focus()
        
        # Bind keyboard shortcuts for voice
        self.root.bind("<KeyPress-space>", self._on_space_press)
        self.root.bind("<KeyRelease-space>", self._on_space_release)
    
    def _on_send_file(self) -> None:
        """Handle send file button click."""
        try:
            # Open file dialog
            file_path = filedialog.askopenfilename(
                title="Select File to Send",
                filetypes=[
                    ("All Files", "*.*"),
                    ("Text Files", "*.txt"),
                    ("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.svg *.webp"),
                    ("Documents", "*.pdf *.doc *.docx *.rtf *.odt"),
                    ("Audio", "*.mp3 *.wav *.ogg *.flac *.aac *.m4a"),
                    ("Video", "*.mp4 *.avi *.mkv *.webm *.mov *.flv"),
                    ("Archives", "*.zip *.rar *.7z *.tar *.gz *.bz2"),
                    ("Code", "*.py *.js *.html *.css *.json *.xml *.csv")
                ]
            )
            
            if file_path and self.on_send_file:
                # Check file size before sending
                file_size = os.path.getsize(file_path)
                max_size = 100 * 1024 * 1024  # 100MB
                
                if file_size > max_size:
                    messagebox.showerror(
                        "File Too Large", 
                        f"File size ({file_size / (1024*1024):.1f} MB) exceeds the maximum limit of 100 MB."
                    )
                    return
                
                # Show confirmation
                filename = os.path.basename(file_path)
                size_mb = file_size / (1024 * 1024)
                
                if messagebox.askyesno(
                    "Send File", 
                    f"Send file '{filename}' ({size_mb:.2f} MB)?\n\n"
                    f"The file will be encrypted and sent securely over the P2P connection."
                ):
                    self.on_send_file(file_path)
                    
        except Exception as e:
            logger.error(f"Error in file selection: {e}")
            messagebox.showerror("Error", f"Failed to select file: {e}")
    
    def _clear_panel(self) -> None:
        """Clear the current panel."""
        if self.current_panel:
            self.current_panel.destroy()
            self.current_panel = None
    
    def _on_create_chat(self) -> None:
        """Handle create chat button click."""
        self._store_username()
        if self.on_create_chat:
            self.on_create_chat()
    
    def _on_join_chat(self) -> None:
        """Handle join chat button click."""
        self._store_username()
        self._show_join_panel()
    
    def _on_join_with_key(self) -> None:
        """Handle join with key submission."""
        if hasattr(self, 'join_entry'):
            invite_key = self.join_entry.get("1.0", "end-1c").strip()
            if invite_key and self.on_join_chat:
                self.on_join_chat(invite_key)
            else:
                messagebox.showwarning("Invalid Input", "Please enter a valid invite key.")
        else:
            messagebox.showerror("Error", "Join input field not found!")
    
    def _on_connect(self) -> None:
        """Handle connect button click."""
        if hasattr(self, 'return_entry'):
            return_key = self.return_entry.get("1.0", "end-1c").strip()
            if return_key and self.on_connect_chat:
                self.on_connect_chat(return_key)
            else:
                messagebox.showwarning("Invalid Input", "Please enter a valid return key.")
        else:
            messagebox.showerror("Error", "Return key input field not found!")
    
    def _on_send(self, event=None) -> None:
        """Handle send message."""
        if hasattr(self, 'message_entry'):
            message = self.message_entry.get().strip()
            if message and self.on_send_message:
                self.on_send_message(message)
                self.message_entry.delete(0, "end")
        return "break"  # Prevent default behavior
    
    def _copy_invite_key(self) -> None:
        """Copy invite key to clipboard."""
        if self.invite_key:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.invite_key)
            # Show temporary feedback
            original_text = self.copy_invite_btn.cget("text")
            self.copy_invite_btn.configure(text="✅ Copied!")
            self.root.after(2000, lambda: self.copy_invite_btn.configure(text=original_text))
    
    def _copy_return_key(self) -> None:
        """Copy return key to clipboard."""
        if self.return_key:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.return_key)
            # Show temporary feedback
            if hasattr(self, 'copy_return_btn'):
                original_text = self.copy_return_btn.cget("text")
                self.copy_return_btn.configure(text="✅ Copied!")
                self.root.after(2000, lambda: self.copy_return_btn.configure(text=original_text))
            print(f"📋 Return key copied to clipboard: {self.return_key[:30]}...")
        else:
            print("❌ No return key to copy!")
    
    def _store_username(self) -> None:
        """Store the current username value."""
        if hasattr(self, 'username_entry'):
            username = self.username_entry.get().strip()
            self.stored_username = username if username else "Anonymous"
    
    # Public interface methods (called by main.py)
    
    def show_create_panel(self, invite_key: str) -> None:
        """Show create panel with the generated invite key."""
        self.invite_key = invite_key
        self._show_create_panel()
        
        # Fix: Use root.after to ensure the panel is fully created first, with a longer delay
        self.root.after(200, lambda: self._populate_invite_key(invite_key))
    
    def _populate_invite_key(self, invite_key: str) -> None:
        """Helper method to populate the invite key field."""
        print(f"🔧 Attempting to populate invite key: {invite_key[:50]}...")
        
        if hasattr(self, 'invite_text') and self.invite_text:
            try:
                # Clear any existing content first
                self.invite_text.delete("0.0", "end")
                # Insert the invite key
                self.invite_text.insert("0.0", invite_key)
                # Set to disabled after populating to prevent editing
                self.invite_text.configure(state="disabled")
                print(f"✅ Invite key populated successfully!")
                
                # Verify the content was set
                content = self.invite_text.get("0.0", "end").strip()
                print(f"   Content verification: {content[:50]}...")
                
            except Exception as e:
                print(f"❌ Error populating invite key: {e}")
                # Try alternative approach
                try:
                    # Enable editing temporarily
                    self.invite_text.configure(state="normal")
                    self.invite_text.delete("1.0", "end") 
                    self.invite_text.insert("1.0", invite_key)
                    self.invite_text.configure(state="disabled")
                    print("✅ Invite key populated using alternative method")
                except Exception as e2:
                    print(f"❌ Alternative method also failed: {e2}")
        else:
            print("❌ invite_text field not found!")
    
    def show_return_key(self, return_key: str) -> None:
        """Display the return key in the join panel."""
        self.return_key = return_key
        print(f"🔧 Showing return key in panel: {return_key[:50]}...")
        
        # Show the return key display frame in the join panel
        if hasattr(self, 'return_display_frame'):
            # Make the return key section visible
            self.return_display_frame.grid(row=2, column=0, sticky="ew", padx=30, pady=10)
            
            # Populate the return key text
            if hasattr(self, 'return_display_text'):
                try:
                    self.return_display_text.configure(state="normal")
                    self.return_display_text.delete("0.0", "end")
                    self.return_display_text.insert("0.0", return_key)
                    self.return_display_text.configure(state="disabled")
                    print("✅ Return key displayed in panel")
                    
                    # Also copy to clipboard automatically
                    self.root.clipboard_clear()
                    self.root.clipboard_append(return_key)
                    
                    # Update status
                    self.set_status("Return key generated - share it with the chat creator! 📤", "green")
                    
                except Exception as e:
                    print(f"❌ Error displaying return key: {e}")
            else:
                print("❌ return_display_text not found!")
        else:
            print("❌ return_display_frame not found!")
            # Fallback to the old popup method if something went wrong
            messagebox.showinfo(
                "Return Key Generated", 
                f"Share this return key with the chat creator:\n\n{return_key}\n\n"
                "This has been copied to your clipboard."
            )
            self.root.clipboard_clear()
            self.root.clipboard_append(return_key)
    
    def show_chat(self) -> None:
        """Transition to the chat interface."""
        self._show_chat_panel()
    
    def add_message(self, message: str, tag: str = None) -> None:
        """Add a message to the chat display with appropriate styling."""
        if hasattr(self, 'chat_display'):
            try:
                # Enable editing temporarily
                self.chat_display.configure(state="normal")
                
                # Configure text tags for different message types with brighter, more readable colors
                self.chat_display.tag_config("sent", foreground="#4A90E2")      # Nice blue for your messages
                self.chat_display.tag_config("received", foreground="#5CB85C")  # Nice green for peer messages  
                self.chat_display.tag_config("system", foreground="#F0AD4E")    # Orange for system messages
                self.chat_display.tag_config("error", foreground="#D9534F")     # Red for error messages
                
                # Insert message with appropriate tag
                if tag:
                    self.chat_display.insert("end", f"{message}\n", tag)
                else:
                    self.chat_display.insert("end", f"{message}\n")
                
                # Scroll to bottom
                self.chat_display.see("end")
                
                # Disable editing again
                self.chat_display.configure(state="disabled")
                
            except Exception as e:
                logger.error(f"Error adding message to chat display: {e}")
                print(f"❌ Error adding message: {e}")
        else:
            # Fallback if chat display not available
            print(f"💬 {message}")
    
    def set_status(self, status: str, color: str = "gray") -> None:
        """Update the status display."""
        status_colors = {
            "green": ("gray30", "gray60"),      # Gray shades instead of colored status
            "red": ("gray40", "gray50"),        # Gray shades instead of red
            "orange": ("gray35", "gray55"),     # Gray shades instead of orange
            "gray": ("gray50", "gray50")
        }
        
        color_tuple = status_colors.get(color, status_colors["gray"])
        self.status_label.configure(text=status, text_color=color_tuple)
    
    def show_error(self, message: str) -> None:
        """Show an error message dialog."""
        messagebox.showerror("Error", message)
    
    def get_username(self) -> str:
        """Get the current username."""
        return self.stored_username if self.stored_username else "Anonymous"
    
    # File transfer event handlers
    
    def show_file_offer(self, offer_data: Dict[str, Any]) -> None:
        """Show file transfer offer dialog."""
        try:
            logger.info(f"Showing file offer dialog for: {offer_data}")
            
            # Validate offer data
            required_fields = ['filename', 'file_size', 'transfer_id']
            for field in required_fields:
                if field not in offer_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create and show dialog
            dialog = FileTransferDialog(
                self.root, 
                offer_data, 
                self._on_accept_file_offer,
                self._on_reject_file_offer
            )
            
            # Make sure dialog is visible
            dialog.deiconify()
            dialog.lift()
            dialog.focus_force()
            
            logger.info("File transfer dialog created and displayed successfully")
            
        except Exception as e:
            logger.error(f"Error showing file offer dialog: {e}")
            # Fallback to simple message box
            filename = offer_data.get('filename', 'Unknown')
            file_size = offer_data.get('file_size', 0)
            size_mb = file_size / (1024 * 1024) if file_size > 0 else 0
            
            result = messagebox.askyesno(
                "File Transfer Offer",
                f"Incoming file transfer:\n\n"
                f"Filename: {filename}\n"
                f"Size: {size_mb:.2f} MB\n\n"
                f"Accept this file transfer?"
            )
            
            if result:
                # Ask for save location
                save_path = filedialog.asksaveasfilename(
                    title="Save File As",
                    initialfile=filename,
                    filetypes=[("All Files", "*.*")]
                )
                if save_path:
                    self._on_accept_file_offer(offer_data['transfer_id'], save_path)
            else:
                self._on_reject_file_offer(offer_data['transfer_id'], "User declined")
    
    def _on_accept_file_offer(self, transfer_id: str, save_path: str) -> None:
        """Handle file offer acceptance."""
        if self.on_accept_file:
            self.on_accept_file(transfer_id, save_path)
    
    def _on_reject_file_offer(self, transfer_id: str, reason: str) -> None:
        """Handle file offer rejection."""
        if self.on_reject_file:
            self.on_reject_file(transfer_id, reason)
    
    def show_file_progress(self, transfer_info: Dict[str, Any]) -> None:
        """Show file transfer progress dialog."""
        try:
            transfer_id = transfer_info.get('transfer_id')
            
            if transfer_id not in self.active_progress_dialogs:
                dialog = FileProgressDialog(self.root, transfer_info)
                self.active_progress_dialogs[transfer_id] = dialog
        except Exception as e:
            logger.error(f"Error showing file progress dialog: {e}")
    
    def update_file_progress(self, progress_data: Dict[str, Any]) -> None:
        """Update file transfer progress."""
        transfer_id = progress_data.get('transfer_id')
        
        if transfer_id in self.active_progress_dialogs:
            try:
                dialog = self.active_progress_dialogs[transfer_id]
                dialog.update_progress(progress_data)
                
                # If transfer is complete, schedule dialog removal
                if progress_data.get('progress', 0) >= 100:
                    self.root.after(3000, lambda: self._remove_progress_dialog(transfer_id))
            except Exception as e:
                logger.error(f"Error updating file progress: {e}")
    
    def _remove_progress_dialog(self, transfer_id: str) -> None:
        """Remove progress dialog after completion."""
        if transfer_id in self.active_progress_dialogs:
            try:
                dialog = self.active_progress_dialogs[transfer_id]
                dialog.destroy()
                del self.active_progress_dialogs[transfer_id]
            except Exception as e:
                logger.warning(f"Error removing progress dialog: {e}")
    
    def show_file_completed(self, completion_data: Dict[str, Any]) -> None:
        """Show file transfer completion notification and move file to final location."""
        filename = completion_data.get('filename', 'Unknown')
        transfer_id = completion_data.get('transfer_id')
        temp_path = completion_data.get('temp_path')
        save_path = completion_data.get('save_path')  # User's pre-chosen save location
        
        # Add message to chat
        timestamp = self._get_timestamp()
        message = f"[{timestamp}] 📁 File received: {filename}"
        self.add_message(message, "system")
        
        # Remove progress dialog
        if transfer_id:
            self._remove_progress_dialog(transfer_id)
        
        # Move file from temp location to user's chosen location
        try:
            if temp_path and os.path.exists(temp_path):
                if save_path:
                    # Use the pre-chosen save path - no need to ask user again
                    # Create directory if it doesn't exist
                    save_dir = os.path.dirname(save_path)
                    if save_dir and not os.path.exists(save_dir):
                        os.makedirs(save_dir, exist_ok=True)
                    
                    # Move file from temp to final location
                    shutil.move(temp_path, save_path)
                    
                    # File moved successfully - no popup needed, just log it
                    logger.info(f"File {filename} saved successfully to {save_path}")
                else:
                    # Fallback: ask user where to save (shouldn't happen with new implementation)
                    save_path = filedialog.asksaveasfilename(
                        title="Save Received File",
                        defaultextension=os.path.splitext(filename)[1],
                        initialfile=filename,
                        filetypes=[
                            ("All Files", "*.*"),
                            ("Text Files", "*.txt"),
                            ("Images", "*.png *.jpg *.jpeg *.gif *.bmp"),
                            ("Documents", "*.pdf *.doc *.docx"),
                            ("Archives", "*.zip *.rar *.7z")
                        ]
                    )
                    
                    if save_path:
                        # Move file from temp to final location
                        shutil.move(temp_path, save_path)
                        
                        # File moved successfully - no popup needed, just log it
                        logger.info(f"File {filename} saved successfully to {save_path}")
                    else:
                        # User cancelled, but show info about temp location
                        messagebox.showinfo(
                            "File Transfer Complete",
                            f"Successfully received: {filename}\n\n"
                            f"File is temporarily stored at: {temp_path}\n"
                            f"Please move it to your desired location."
                        )
            else:
                # Temp file not found
                messagebox.showwarning(
                    "File Transfer Issue",
                    f"File transfer completed but temporary file not found.\n"
                    f"The file may have been moved or deleted."
                )
        except Exception as e:
            logger.error(f"Error handling completed file: {e}")
            messagebox.showerror(
                "File Transfer Error",
                f"File transfer completed but failed to save:\n{e}\n\n"
                f"Temporary file location: {temp_path}"
            )
    
    def show_file_error(self, error_data: Dict[str, Any]) -> None:
        """Show file transfer error."""
        error_msg = error_data.get('error', 'Unknown error')
        transfer_id = error_data.get('transfer_id')
        
        # Add error message to chat
        timestamp = self._get_timestamp()
        message = f"[{timestamp}] ❌ File transfer error: {error_msg}"
        self.add_message(message, "error")
        
        # Remove progress dialog if exists
        if transfer_id:
            self._remove_progress_dialog(transfer_id)
        
        # Show error dialog
        messagebox.showerror("File Transfer Error", f"File transfer failed:\n{error_msg}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        return datetime.now().strftime("%H:%M:%S")

    def _on_voice_enable_toggle(self) -> None:
        """Handle voice enable/disable button click."""
        if self.voice_enabled:
            # Disable voice chat
            self.voice_enabled = False
            self.voice_enable_btn.configure(text="🎤 Voice", fg_color=("gray60", "gray40"))
            self.voice_ptt_btn.configure(state="disabled")
            self.voice_status_label.grid_remove()  # Hide status when disabled
            if self.on_disable_voice:
                self.on_disable_voice()
        else:
            # Enable voice chat
            self.voice_enabled = True
            self.voice_enable_btn.configure(text="🎤 On", fg_color=("gray45", "gray35"))
            self.voice_ptt_btn.configure(state="normal")
            # Show compact status
            self.voice_status_label.configure(text="💡 Hold 'Talk' button or SPACE (when not typing) to transmit")
            self.voice_status_label.grid(row=2, column=0, sticky="ew", pady=(5, 0))
            if self.on_enable_voice:
                self.on_enable_voice()

    def _on_voice_start(self, event) -> None:
        """Handle voice start event."""
        if not self.voice_enabled:
            return
        
        self.voice_transmitting = True
        self.voice_ptt_btn.configure(text="🔴 ON", fg_color=("gray50", "gray30"))
        self.voice_status_label.configure(text="🔴 Transmitting audio...")
        if self.on_start_voice_transmission:
            self.on_start_voice_transmission()

    def _on_voice_stop(self, event) -> None:
        """Handle voice stop event."""
        if not self.voice_enabled:
            return
            
        self.voice_transmitting = False
        self.voice_ptt_btn.configure(text="🗣️ Talk", fg_color=("gray40", "gray40"))
        self.voice_status_label.configure(text="💡 Hold 'Talk' button or SPACE (when not typing) to transmit")
        if self.on_stop_voice_transmission:
            self.on_stop_voice_transmission()

    def _on_space_press(self, event) -> None:
        """Handle space key press for push-to-talk."""
        if self.voice_enabled and not self.voice_transmitting and hasattr(self, 'message_entry'):
            # Only activate if not typing in text field
            if self.root.focus_get() != self.message_entry:
                self._on_voice_start(event)

    def _on_space_release(self, event) -> None:
        """Handle space key release for push-to-talk."""
        if self.voice_enabled and self.voice_transmitting and hasattr(self, 'message_entry'):
            # Only deactivate if not typing in text field
            if self.root.focus_get() != self.message_entry:
                self._on_voice_stop(event)

    def update_voice_status(self, status: str) -> None:
        """Update voice status from external source."""
        if hasattr(self, 'voice_status_label'):
            self.voice_status_label.configure(text=f"Voice Chat: {status}")

    def set_voice_enabled(self, enabled: bool) -> None:
        """Set voice enabled state from external source."""
        self.voice_enabled = enabled
        if hasattr(self, 'voice_enable_btn'):
            self.voice_enable_btn.configure(
                text="🎤 On" if enabled else "🎤 Voice",
                fg_color=("gray45", "gray35") if enabled else ("gray60", "gray40")
            )
        if hasattr(self, 'voice_ptt_btn'):
            self.voice_ptt_btn.configure(state="normal" if enabled else "disabled")
        if hasattr(self, 'voice_status_label'):
            if enabled:
                self.voice_status_label.configure(text="💡 Hold 'Talk' button or SPACE (when not typing) to transmit")
                self.voice_status_label.grid(row=2, column=0, sticky="ew", pady=(5, 0))
            else:
                self.voice_status_label.grid_remove()

    def _on_disconnect(self) -> None:
        """Handle disconnect button click."""
        try:
            if self.on_disconnect_chat:
                self.on_disconnect_chat()
            # Return to start panel
            self._show_start_panel()
            self.set_status("Disconnected from chat", "gray")
        except Exception as e:
            logger.error(f"Error disconnecting from chat: {e}")
            self.show_error(f"Failed to disconnect: {e}")

    def _on_space_press(self, event) -> None:
        """Handle space key press for push-to-talk."""
        if self.voice_enabled and not self.voice_transmitting and hasattr(self, 'message_entry'):
            # Only activate if not typing in text field
            if self.root.focus_get() != self.message_entry:
                self._on_voice_start(event)

    def _on_space_release(self, event) -> None:
        """Handle space key release for push-to-talk."""
        if self.voice_enabled and self.voice_transmitting and hasattr(self, 'message_entry'):
            # Only deactivate if not typing in text field
            if self.root.focus_get() != self.message_entry:
                self._on_voice_stop(event)

    def update_voice_status(self, status: str) -> None:
        """Update voice status from external source."""
        if hasattr(self, 'voice_status_label'):
            self.voice_status_label.configure(text=f"Voice Chat: {status}")

    def set_voice_enabled(self, enabled: bool) -> None:
        """Set voice enabled state from external source."""
        self.voice_enabled = enabled
        if hasattr(self, 'voice_enable_btn'):
            self.voice_enable_btn.configure(
                text="🎤 On" if enabled else "🎤 Voice",
                fg_color=("gray45", "gray35") if enabled else ("gray60", "gray40")
            )
        if hasattr(self, 'voice_ptt_btn'):
            self.voice_ptt_btn.configure(state="normal" if enabled else "disabled")
        if hasattr(self, 'voice_status_label'):
            if enabled:
                self.voice_status_label.configure(text="💡 Hold 'Talk' button or SPACE (when not typing) to transmit")
                self.voice_status_label.grid(row=2, column=0, sticky="ew", pady=(5, 0))
            else:
                self.voice_status_label.grid_remove()

    def _on_voice_toggle_mode(self) -> None:
        """Handle voice toggle mode button click (for toggle instead of push-to-talk)."""
        if not self.voice_enabled:
            return
            
        if self.voice_transmitting:
            # Stop transmitting
            self._on_voice_stop(None)
            self.voice_ptt_btn.configure(text="🔄 Start Talk")
        else:
            # Start transmitting
            self._on_voice_start(None) 
            self.voice_ptt_btn.configure(text="🔄 Stop Talk")

    def _on_space_press(self, event) -> None:
        """Handle space key press for push-to-talk."""
        if self.voice_enabled and not self.voice_transmitting and hasattr(self, 'message_entry'):
            # Only activate if not typing in text field
            if self.root.focus_get() != self.message_entry:
                self._on_voice_start(event)

    def _on_space_release(self, event) -> None:
        """Handle space key release for push-to-talk."""
        if self.voice_enabled and self.voice_transmitting and hasattr(self, 'message_entry'):
            # Only deactivate if not typing in text field
            if self.root.focus_get() != self.message_entry:
                self._on_voice_stop(event)

    def update_voice_status(self, status: str) -> None:
        """Update voice status from external source."""
        if hasattr(self, 'voice_status_label'):
            self.voice_status_label.configure(text=f"Voice Chat: {status}")

    def set_voice_enabled(self, enabled: bool) -> None:
        """Set voice enabled state from external source."""
        self.voice_enabled = enabled
        if hasattr(self, 'voice_enable_btn'):
            self.voice_enable_btn.configure(
                text="🎤 On" if enabled else "🎤 Voice",
                fg_color=("gray45", "gray35") if enabled else ("gray60", "gray40")
            )
        if hasattr(self, 'voice_ptt_btn'):
            self.voice_ptt_btn.configure(state="normal" if enabled else "disabled")
        if hasattr(self, 'voice_status_label'):
            if enabled:
                self.voice_status_label.configure(text="💡 Hold 'Talk' button or SPACE (when not typing) to transmit")
                self.voice_status_label.grid(row=2, column=0, sticky="ew", pady=(5, 0))
            else:
                self.voice_status_label.grid_remove() 
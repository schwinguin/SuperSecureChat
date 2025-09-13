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
from .connection_settings_dialog import ConnectionSettingsDialog
from .connection_wizard import ConnectionWizard

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
        # Removed separate transmission callbacks - now using simple toggle
        
        # Audio settings callback
        self.on_audio_settings_changed: Optional[Callable] = None
        
        # Connection settings callback
        self.on_connection_settings_changed: Optional[Callable] = None
        
        # Settings storage
        self.current_audio_settings: Dict[str, Any] = {}
        self.current_connection_settings: Dict[str, Any] = {}
        
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
        
        # User list tracking
        self.connected_users: Dict[str, Dict[str, Any]] = {}
        self.local_username = "You"
        
        # Connection wizard
        self.connection_wizard: Optional[ConnectionWizard] = None
        
        self._setup_ui()
        self._show_connection_wizard()
    
    def _setup_ui(self) -> None:
        """Set up the main UI structure with simplified design."""
        # Configure grid weights
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)  # Status bar row
        
        # Single main container - removed unnecessary main_frame wrapper
        self.panel_frame = ctk.CTkFrame(self.root, corner_radius=0)
        self.panel_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 0))
        self.panel_frame.grid_columnconfigure(0, weight=1)
        self.panel_frame.grid_rowconfigure(1, weight=1)
        
        # Title and burger menu frame
        title_frame = ctk.CTkFrame(self.panel_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(20, 10))
        title_frame.grid_columnconfigure(0, weight=1)  # Center column
        title_frame.grid_columnconfigure(1, weight=0)  # Fixed width for button
        
        # Simple title - centered
        title_label = ctk.CTkLabel(
            title_frame,
            text="🔒 P2P Secure Chat",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, sticky="")
        
        # Burger menu button
        self.burger_menu_button = ctk.CTkButton(
            title_frame,
            text="☰",
            width=40,
            height=40,
            command=self._toggle_burger_menu,
            font=ctk.CTkFont(size=18, weight="bold"),
            corner_radius=8,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40")
        )
        self.burger_menu_button.grid(row=0, column=1, sticky="e", padx=(10, 20))
        
        # Burger menu dropdown (initially hidden) - use toplevel window
        self.burger_menu_window = None
        self.burger_menu_visible = False
        
        # Content area - removed panel_frame wrapper
        self.content_frame = ctk.CTkFrame(self.panel_frame, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Status bar at the very bottom of the window
        status_frame = ctk.CTkFrame(self.root, height=40, corner_radius=0, fg_color=("gray20", "gray20"))
        status_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray50")
        )
        self.status_label.grid(row=0, column=0, pady=8)
    
    def _toggle_burger_menu(self):
        """Toggle the burger menu dropdown."""
        if self.burger_menu_visible:
            self._hide_burger_menu()
        else:
            self._show_burger_menu()
    
    def _show_burger_menu(self):
        """Show the burger menu dropdown."""
        if not self.burger_menu_visible:
            # Create frame for menu within the main window
            self.burger_menu_frame = ctk.CTkFrame(
                self.root,
                width=220,
                height=140,
                fg_color=("gray95", "gray15"),
                corner_radius=0
            )
            
            # Position the menu frame
            self._position_burger_menu()
            
            # Create menu items
            self._create_burger_menu_items()
            
            self.burger_menu_visible = True
            # Bind click outside to close menu
            self.root.after(100, lambda: self.root.bind("<Button-1>", self._on_click_outside_menu))
    
    def _hide_burger_menu(self):
        """Hide the burger menu dropdown."""
        if self.burger_menu_visible and self.burger_menu_frame:
            self.burger_menu_frame.destroy()
            self.burger_menu_frame = None
            self.burger_menu_visible = False
            # Unbind click outside
            self.root.unbind("<Button-1>")
    
    def _position_burger_menu(self):
        """Position the burger menu in the top right corner."""
        try:
            # Get the burger button position relative to the main window
            button_x = self.burger_menu_button.winfo_x()
            button_y = self.burger_menu_button.winfo_y()
            button_height = self.burger_menu_button.winfo_height()
            
            # Calculate menu position (below the button, aligned to the right)
            menu_x = button_x - 180  # 220px width - 40px button width = 180px offset
            menu_y = button_y + button_height + 5  # 5px gap below button
            
            # Position the frame using place()
            self.burger_menu_frame.place(x=menu_x, y=menu_y)
            
            print(f"Menu positioned at: x={menu_x}, y={menu_y}")
        except Exception as e:
            print(f"Error positioning burger menu: {e}")
    
    def _create_burger_menu_items(self):
        """Create the burger menu items."""
        # Configure the frame
        self.burger_menu_frame.grid_columnconfigure(0, weight=1)
        
        # Connection settings button
        connection_btn = ctk.CTkButton(
            self.burger_menu_frame,
            text="🌐 Connection Settings",
            width=200,
            height=35,
            command=self._on_burger_connection_settings,
            corner_radius=8,
            font=ctk.CTkFont(size=14),
            fg_color=("gray80", "gray25"),
            hover_color=("gray70", "gray35")
        )
        connection_btn.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        
        # Audio settings button
        audio_btn = ctk.CTkButton(
            self.burger_menu_frame,
            text="🎵 Audio Settings",
            width=200,
            height=35,
            command=self._on_burger_audio_settings,
            corner_radius=8,
            font=ctk.CTkFont(size=14),
            fg_color=("gray80", "gray25"),
            hover_color=("gray70", "gray35")
        )
        audio_btn.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        # Theme toggle button
        theme_btn = ctk.CTkButton(
            self.burger_menu_frame,
            text="🌙 Toggle Theme",
            width=200,
            height=35,
            command=self._on_burger_theme_toggle,
            corner_radius=8,
            font=ctk.CTkFont(size=14),
            fg_color=("gray80", "gray25"),
            hover_color=("gray70", "gray35")
        )
        theme_btn.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="ew")
    
    def _on_click_outside_menu(self, event):
        """Handle clicks outside the burger menu to close it."""
        try:
            if self.burger_menu_frame and self.burger_menu_frame.winfo_exists():
                # Get the menu frame geometry
                menu_x = self.burger_menu_frame.winfo_rootx()
                menu_y = self.burger_menu_frame.winfo_rooty()
                menu_width = self.burger_menu_frame.winfo_width()
                menu_height = self.burger_menu_frame.winfo_height()
                
                # Get the button geometry
                button_x = self.burger_menu_button.winfo_rootx()
                button_y = self.burger_menu_button.winfo_rooty()
                button_width = self.burger_menu_button.winfo_width()
                button_height = self.burger_menu_button.winfo_height()
                
                # Check if click is outside both the menu and button
                outside_menu = not (menu_x <= event.x_root <= menu_x + menu_width and 
                                  menu_y <= event.y_root <= menu_y + menu_height)
                outside_button = not (button_x <= event.x_root <= button_x + button_width and 
                                    button_y <= event.y_root <= button_y + button_height)
                
                if outside_menu and outside_button:
                    self._hide_burger_menu()
        except:
            # If there's an error checking coordinates, just hide the menu
            self._hide_burger_menu()
    
    def _on_burger_connection_settings(self):
        """Handle connection settings from burger menu."""
        self._hide_burger_menu()
        self._show_connection_settings()
    
    def _on_burger_audio_settings(self):
        """Handle audio settings from burger menu."""
        self._hide_burger_menu()
        self._show_audio_settings()
    
    def _on_burger_theme_toggle(self):
        """Handle theme toggle from burger menu."""
        self._hide_burger_menu()
        self._toggle_theme()
    
    def _toggle_theme(self):
        """Toggle between dark and light themes."""
        current = ctk.get_appearance_mode()
        new_mode = "light" if current == "Dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        
        # Update theme button emoji in burger menu if visible
        if self.burger_menu_visible:
            # Find and update the theme button in the burger menu
            for widget in self.burger_menu_frame.winfo_children():
                if isinstance(widget, ctk.CTkButton) and "Toggle Theme" in widget.cget("text"):
                    widget.configure(text="☀️ Toggle Theme" if new_mode == "dark" else "🌙 Toggle Theme")
                    break
    
    def _show_connection_settings(self):
        """Show the connection settings dialog."""
        try:
            dialog = ConnectionSettingsDialog(self.root, self.current_connection_settings)
            dialog.on_settings_saved = self._on_connection_settings_saved
            dialog.show()
        except Exception as e:
            logger.error(f"Failed to show connection settings: {e}")
            messagebox.showerror("Error", f"Failed to open connection settings:\n{e}")
    
    def _on_connection_settings_saved(self, settings: Dict[str, Any]):
        """Handle connection settings being saved."""
        self.current_connection_settings.update(settings)
        logger.info(f"Connection settings updated in GUI: {settings}")
        
        # Notify the main application
        if self.on_connection_settings_changed:
            self.on_connection_settings_changed(settings)
    
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
    
    def set_connection_settings(self, settings: Dict[str, Any]):
        """Set the current connection settings from external source."""
        self.current_connection_settings = settings
    
    def _show_start_panel(self) -> None:
        """Show the simplified start panel with Create/Join buttons."""
        self._clear_panel()
        
        # Single content panel without extra wrappers
        panel = ctk.CTkFrame(self.content_frame, corner_radius=0)
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
        panel = ctk.CTkScrollableFrame(self.content_frame, corner_radius=0)
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
            width=160,  # Fixed width to prevent shifting
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
            corner_radius=0
        )
        self.return_entry.grid(row=6, column=0, sticky="ew", padx=20, pady=(0, 10))
        
        # Set up placeholder text for return entry
        self.return_entry_placeholder = "Paste the return key from your peer here..."
        self._setup_placeholder_text(self.return_entry, self.return_entry_placeholder)
        
        self.connect_btn = ctk.CTkButton(
            panel,
            text="🔗 Connect Now",
            width=160,  # Fixed width to prevent shifting
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
            text="← Back to Wizard",
            width=150,
            height=35,
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            command=self._show_connection_wizard,
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
        panel = ctk.CTkFrame(self.content_frame, corner_radius=0)
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
            corner_radius=0
        )
        self.join_entry.grid(row=3, column=0, sticky="ew", padx=30, pady=(0, 10))
        
        # Set up placeholder text for join entry
        self.join_entry_placeholder = "Paste the invite key here..."
        self._setup_placeholder_text(self.join_entry, self.join_entry_placeholder)
        
        self.join_submit_btn = ctk.CTkButton(
            panel,
            text="🚀 Join Chat",
            width=160,  # Fixed width to prevent shifting
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=8,
            command=self._on_join_with_key,
            fg_color=("gray50", "gray30"),  # Background shade instead of gold
            hover_color=("gray60", "gray20")
        )
        self.join_submit_btn.grid(row=4, column=0, pady=(0, 30))
        
        # Return key display section (initially hidden)
        self.return_display_frame = ctk.CTkFrame(panel, corner_radius=0)
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
            width=160,  # Fixed width to prevent shifting
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
            text="← Back to Wizard",
            width=150,
            height=35,
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            command=self._show_connection_wizard,
            fg_color=("gray60", "gray40"),
            hover_color=("gray50", "gray50")
        ).grid(row=6, column=0, pady=30)
        
        self.current_panel = panel
        print("✅ Join panel setup complete")
    
    def _show_connection_wizard(self) -> None:
        """Show the connection wizard instead of the start panel."""
        self._clear_panel()
        
        # Create a dedicated wizard frame that won't interfere with content_frame
        self.wizard_container = ctk.CTkFrame(self.panel_frame, corner_radius=0, fg_color="transparent")
        self.wizard_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.wizard_container.grid_columnconfigure(0, weight=1)
        self.wizard_container.grid_rowconfigure(0, weight=1)
        
        # Create and show the connection wizard
        self.connection_wizard = ConnectionWizard(self.wizard_container)
        
        # Set up wizard callbacks
        self.connection_wizard.on_create_chat = self._on_wizard_create_chat
        self.connection_wizard.on_join_chat = self._on_wizard_join_chat
        self.connection_wizard.on_connect_chat = self._on_wizard_connect_chat
        self.connection_wizard.on_wizard_complete = self._on_wizard_complete
        self.connection_wizard.on_wizard_cancel = self._on_wizard_cancel
        
        self.connection_wizard.show()
        
        # Set current panel to track wizard state
        self.current_panel = self.panel_frame
    
    def _on_wizard_create_chat(self) -> None:
        """Handle create chat from wizard."""
        if self.on_create_chat:
            self.on_create_chat()
    
    def _on_wizard_join_chat(self, invite_key: str) -> None:
        """Handle join chat from wizard."""
        if self.on_join_chat:
            self.on_join_chat(invite_key)
    
    def _on_wizard_connect_chat(self, return_key: str) -> None:
        """Handle connect chat from wizard."""
        if self.on_connect_chat:
            self.on_connect_chat(return_key)
    
    def _on_wizard_complete(self) -> None:
        """Handle wizard completion - transition to chat."""
        # Clean up wizard container
        if hasattr(self, 'wizard_container') and self.wizard_container:
            self.wizard_container.destroy()
            self.wizard_container = None
        
        # Ensure content frame is properly recreated after wizard cleanup
        self._recreate_content_frame()
        self._show_chat_panel()
    
    def _on_wizard_cancel(self) -> None:
        """Handle wizard cancellation - show start panel as fallback."""
        # Clean up wizard container
        if hasattr(self, 'wizard_container') and self.wizard_container:
            self.wizard_container.destroy()
            self.wizard_container = None
        
        self._show_start_panel()
    
    def _show_chat_panel(self) -> None:
        """Show the enhanced chat interface with file transfer, voice chat, and user list capabilities."""
        self._clear_panel()
        
        # Ensure content frame exists and is valid
        if not hasattr(self, 'content_frame') or not self.content_frame or not self.content_frame.winfo_exists():
            self._recreate_content_frame()
        
        # Main panel for chat with two columns: chat area and user list
        panel = ctk.CTkFrame(self.content_frame, corner_radius=0)
        panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        panel.grid_columnconfigure(0, weight=1)  # Chat area takes most space
        panel.grid_columnconfigure(1, weight=0)  # User list has fixed width
        panel.grid_rowconfigure(0, weight=1)
        
        # Chat area frame
        chat_frame = ctk.CTkFrame(panel, corner_radius=0, fg_color="transparent")
        chat_frame.grid(row=0, column=0, sticky="nsew", padx=(15, 5), pady=15)
        chat_frame.grid_columnconfigure(0, weight=1)
        chat_frame.grid_rowconfigure(0, weight=1)  # Chat display gets most space
        chat_frame.grid_rowconfigure(1, weight=0)  # Input frame has fixed height
        
        # Chat display area
        self.chat_display = ctk.CTkTextbox(
            chat_frame,
            corner_radius=8,
            font=ctk.CTkFont(size=16),  # Keep larger font for readability
            state="disabled",
            wrap="word"
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew")
        
        # User list sidebar
        user_list_frame = ctk.CTkFrame(panel, corner_radius=0, width=200)
        user_list_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 15), pady=15)
        user_list_frame.grid_columnconfigure(0, weight=1)
        user_list_frame.grid_rowconfigure(1, weight=1)
        user_list_frame.grid_propagate(False)  # Maintain fixed width
        
        # User list header
        user_list_header = ctk.CTkLabel(
            user_list_frame,
            text="👥 Participants",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("gray20", "gray80")
        )
        user_list_header.grid(row=0, column=0, pady=(10, 5), padx=10)
        
        # User list display
        self.user_list_display = ctk.CTkTextbox(
            user_list_frame,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            state="disabled",
            height=100,
            fg_color=("gray90", "gray20")
        )
        self.user_list_display.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Connection info
        self.connection_info = ctk.CTkLabel(
            user_list_frame,
            text="🔗 Connection: P2P\n🔒 Encrypted",
            font=ctk.CTkFont(size=10),
            text_color=("gray40", "gray60"),
            justify="left"
        )
        self.connection_info.grid(row=2, column=0, pady=(0, 10), padx=10)

        # Input and controls frame (compact) - positioned under chat area
        input_frame = ctk.CTkFrame(chat_frame, fg_color="transparent")
        input_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        input_frame.grid_columnconfigure(0, weight=1)

        # Message input (smaller)
        self.message_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type your message here... (Press Enter to send)",
            font=ctk.CTkFont(size=14),
            height=35,  # Reduced from 45
            corner_radius=0
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
            corner_radius=8,
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
            corner_radius=8,
            command=self._on_send_file,
            fg_color=("gray45", "gray35"),
            hover_color=("gray55", "gray25")
        )
        self.file_btn.grid(row=0, column=1, padx=5, sticky="w")

        # Voice enable button (fixed width to prevent shifting)
        self.voice_enable_btn = ctk.CTkButton(
            button_row,
            text="🎤 Start Voice Chat",
            width=140,  # Fixed width to accommodate both text states
            height=32,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8,
            command=self._on_voice_enable_toggle,
            fg_color=("gray60", "gray40"),
            hover_color=("gray50", "gray50")
        )
        self.voice_enable_btn.grid(row=0, column=2, padx=5, sticky="w")

        # Removed push-to-talk button - now using simple voice toggle

        # Disconnect button (compact, right side)
        self.disconnect_btn = ctk.CTkButton(
            button_row,
            text="🚪 Leave",
            width=70,
            height=32,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8,
            command=self._on_disconnect,
            fg_color=("gray40", "gray40"),
            hover_color=("gray50", "gray30")
        )
        self.disconnect_btn.grid(row=0, column=4, sticky="e")

        # Removed voice status label to prevent UI shifting

        self.current_panel = panel
        
        # Focus on message entry
        self.message_entry.focus()
        
        # Removed keyboard shortcuts - now using simple voice toggle
    
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
    
    def _recreate_content_frame(self) -> None:
        """Recreate the content frame after wizard cleanup."""
        # Destroy existing content frame if it exists
        if hasattr(self, 'content_frame') and self.content_frame:
            try:
                self.content_frame.destroy()
            except:
                pass  # Frame may already be destroyed
        
        # Ensure panel_frame exists and is valid
        if not hasattr(self, 'panel_frame') or not self.panel_frame or not self.panel_frame.winfo_exists():
            self._recreate_panel_frame()
        
        # Recreate content frame
        self.content_frame = ctk.CTkFrame(self.panel_frame, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
    
    def _recreate_panel_frame(self) -> None:
        """Recreate the panel frame if it has been destroyed."""
        # Destroy existing panel frame if it exists
        if hasattr(self, 'panel_frame') and self.panel_frame:
            try:
                self.panel_frame.destroy()
            except:
                pass  # Frame may already be destroyed
        
        # Recreate panel frame
        self.panel_frame = ctk.CTkFrame(self.root, corner_radius=0)
        self.panel_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 0))
        self.panel_frame.grid_columnconfigure(0, weight=1)
        self.panel_frame.grid_rowconfigure(1, weight=1)
        
        # Recreate title and burger menu frame
        title_frame = ctk.CTkFrame(self.panel_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(20, 10))
        title_frame.grid_columnconfigure(0, weight=1)  # Center column
        title_frame.grid_columnconfigure(1, weight=0)  # Fixed width for button
        
        # Recreate title - centered
        title_label = ctk.CTkLabel(
            title_frame,
            text="🔒 P2P Secure Chat",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, sticky="")
        
        # Recreate burger menu button
        self.burger_menu_button = ctk.CTkButton(
            title_frame,
            text="☰",
            width=40,
            height=40,
            command=self._toggle_burger_menu,
            font=ctk.CTkFont(size=18, weight="bold"),
            corner_radius=8,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40")
        )
        self.burger_menu_button.grid(row=0, column=1, sticky="e", padx=(10, 20))
        
        # Recreate burger menu dropdown (initially hidden) - use frame
        self.burger_menu_frame = None
        self.burger_menu_visible = False
    
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
            invite_key = self._get_textbox_content(self.join_entry)
            if invite_key and self.on_join_chat:
                self.on_join_chat(invite_key)
            else:
                messagebox.showwarning("Invalid Input", "Please enter a valid invite key.")
        else:
            messagebox.showerror("Error", "Join input field not found!")
    
    def _on_connect(self) -> None:
        """Handle connect button click."""
        if hasattr(self, 'return_entry'):
            return_key = self._get_textbox_content(self.return_entry)
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
        
        # If wizard is active, update it
        if self.connection_wizard:
            self.connection_wizard.set_invite_key(invite_key)
        else:
            # Fallback to old method
            self._show_create_panel()
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
        
        # If wizard is active, update it
        if self.connection_wizard:
            self.connection_wizard.set_return_key(return_key)
            # Also copy to clipboard automatically
            self.root.clipboard_clear()
            self.root.clipboard_append(return_key)
            # Update status
            self.set_status("Return key generated - share it with the chat creator! 📤", "green")
        else:
            # Fallback to old method
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
        # Complete the wizard if it's active
        if self.connection_wizard:
            self.connection_wizard.complete_wizard()
        else:
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
        # If wizard is active, get username from wizard
        if self.connection_wizard:
            return self.connection_wizard.get_username()
        return self.stored_username if self.stored_username else "Anonymous"
    
    # User list management methods
    
    def update_user_list(self, users: Dict[str, Dict[str, Any]]) -> None:
        """Update the user list display."""
        if hasattr(self, 'user_list_display'):
            try:
                self.user_list_display.configure(state="normal")
                self.user_list_display.delete("1.0", "end")
                
                # Add all users (including local user)
                for user_id, user_info in users.items():
                    username = user_info.get('username', 'Peer')
                    status = user_info.get('status', 'online')
                    voice_status = user_info.get('voice_enabled', False)
                    
                    # Special handling for local user
                    if user_id == "local_001":
                        status_icon = "🟢"
                        status_text = "Online (You)"
                    else:
                        status_icon = "🟢" if status == "online" else "🔴"
                        status_text = "Online"
                    
                    voice_icon = " 🎤" if voice_status else ""
                    
                    self.user_list_display.insert("end", f"{username}\n{status_icon} {status_text}{voice_icon}\n\n")
                
                self.user_list_display.configure(state="disabled")
                
            except Exception as e:
                logger.error(f"Error updating user list: {e}")
    
    def add_user(self, user_id: str, username: str, status: str = "online") -> None:
        """Add a user to the connected users list."""
        self.connected_users[user_id] = {
            'username': username,
            'status': status,
            'voice_enabled': False,
            'connected_at': datetime.now()
        }
        self.update_user_list(self.connected_users)
        
        # Add system message about user joining (but not for local user or generic "Peer" placeholder)
        if username != "Peer" and user_id != "local_001":
            timestamp = datetime.now().strftime("%H:%M:%S")
            join_message = f"[{timestamp}] 👋 {username} joined the chat"
            self.add_message(join_message, "system")
    
    def remove_user(self, user_id: str) -> None:
        """Remove a user from the connected users list."""
        if user_id in self.connected_users:
            username = self.connected_users[user_id].get('username', 'Unknown')
            del self.connected_users[user_id]
            self.update_user_list(self.connected_users)
            
            # Add system message about user leaving
            timestamp = datetime.now().strftime("%H:%M:%S")
            leave_message = f"[{timestamp}] 👋 {username} left the chat"
            self.add_message(leave_message, "system")
    
    def update_user_voice_status(self, user_id: str, voice_enabled: bool) -> None:
        """Update a user's voice chat status."""
        if user_id in self.connected_users:
            self.connected_users[user_id]['voice_enabled'] = voice_enabled
            self.update_user_list(self.connected_users)
    
    def update_user_username(self, user_id: str, new_username: str) -> None:
        """Update a user's username."""
        if user_id in self.connected_users:
            old_username = self.connected_users[user_id].get('username', 'Unknown')
            self.connected_users[user_id]['username'] = new_username
            self.update_user_list(self.connected_users)
            logger.info(f"Updated user {user_id} username from '{old_username}' to '{new_username}'")
    
    def set_local_username(self, username: str) -> None:
        """Set the local username and update display."""
        self.local_username = username
        self.stored_username = username
        self.update_user_list(self.connected_users)
    
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
        """Handle voice chat toggle - simple on/off switch."""
        if self.voice_enabled and self.voice_transmitting:
            # Stop voice chat (disable and stop transmission)
            self.voice_enabled = False
            self.voice_transmitting = False
            
            # Update local user's voice status in connected_users
            if "local_001" in self.connected_users:
                self.connected_users["local_001"]["voice_enabled"] = False
            
            self.voice_enable_btn.configure(text="🎤 Start Voice Chat", fg_color=("gray60", "gray40"))
            # Removed voice status label to prevent UI shifting
            if self.on_disable_voice:
                self.on_disable_voice()
        else:
            # Start voice chat (enable and start transmission immediately)
            self.voice_enabled = True
            self.voice_transmitting = True
            
            # Update local user's voice status in connected_users
            if "local_001" in self.connected_users:
                self.connected_users["local_001"]["voice_enabled"] = True
            
            self.voice_enable_btn.configure(text="🔇 Stop Voice Chat", fg_color=("red", "darkred"))
            # Removed voice status label to prevent UI shifting
            if self.on_enable_voice:
                self.on_enable_voice()
        
        # Update user list to reflect voice status change
        if hasattr(self, 'update_user_list'):
            self.update_user_list(self.connected_users)

    # Removed push-to-talk methods - now using simple toggle

    # Removed update_voice_status - no longer needed

    def set_voice_enabled(self, enabled: bool) -> None:
        """Set voice enabled state from external source."""
        self.voice_enabled = enabled
        
        # Update local user's voice status in connected_users
        if "local_001" in self.connected_users:
            self.connected_users["local_001"]["voice_enabled"] = enabled
        
        if hasattr(self, 'voice_enable_btn'):
            if enabled:
                self.voice_enable_btn.configure(
                    text="🔇 Stop Voice Chat",
                    fg_color=("red", "darkred")
                )
            else:
                self.voice_enable_btn.configure(
                    text="🎤 Start Voice Chat",
                    fg_color=("gray60", "gray40")
                )
        # Removed voice_ptt_btn references - using simple toggle now
        # Removed voice status label to prevent UI shifting
        
        # Update user list to reflect voice status change
        if hasattr(self, 'update_user_list'):
            self.update_user_list(self.connected_users)

    def _on_disconnect(self) -> None:
        """Handle disconnect button click."""
        try:
            if self.on_disconnect_chat:
                self.on_disconnect_chat()
            # Return to connection wizard instead of start panel
            self._show_connection_wizard()
            self.set_status("Disconnected from chat", "gray")
        except Exception as e:
            logger.error(f"Error disconnecting from chat: {e}")
            self.show_error(f"Failed to disconnect: {e}")
    
    def reset_wizard_state(self) -> None:
        """Reset the connection wizard to initial state."""
        try:
            if self.connection_wizard:
                # Reset wizard state
                self.connection_wizard.current_step = self.connection_wizard.WizardStep.WELCOME
                self.connection_wizard.step_history.clear()
                self.connection_wizard.connection_type = None
                self.connection_wizard.invite_key = ""
                self.connection_wizard.return_key = ""
                
                # Show the welcome step
                self.connection_wizard._show_step(self.connection_wizard.WizardStep.WELCOME)
                
                logger.info("Wizard state reset to initial state")
        except Exception as e:
            logger.error(f"Error resetting wizard state: {e}") 
    # Placeholder text handling methods
    
    def _setup_placeholder_text(self, textbox: ctk.CTkTextbox, placeholder: str) -> None:
        """Set up placeholder text for a CTkTextbox that disappears when user types."""
        # Store the placeholder text as an attribute
        textbox._placeholder_text = placeholder
        textbox._is_placeholder = True
        
        # Insert placeholder text initially
        textbox.insert("0.0", placeholder)
        textbox.configure(text_color=("gray50", "gray50"))  # Gray color for placeholder
        
        # Bind events
        textbox.bind("<Button-1>", lambda e: self._on_textbox_click(textbox))
        textbox.bind("<KeyPress>", lambda e: self._on_textbox_keypress(textbox, e))
        textbox.bind("<Control-v>", lambda e: self._on_textbox_paste(textbox, e))
        textbox.bind("<Shift-Insert>", lambda e: self._on_textbox_paste(textbox, e))
        textbox.bind("<FocusOut>", lambda e: self._on_textbox_focus_out(textbox))
    
    def _on_textbox_click(self, textbox: ctk.CTkTextbox) -> None:
        """Handle click on textbox with placeholder text."""
        if getattr(textbox, '_is_placeholder', False):
            self._clear_placeholder(textbox)
    
    def _on_textbox_keypress(self, textbox: ctk.CTkTextbox, event) -> None:
        """Handle key press on textbox with placeholder text."""
        if getattr(textbox, '_is_placeholder', False):
            self._clear_placeholder(textbox)
    
    def _on_textbox_paste(self, textbox: ctk.CTkTextbox, event) -> None:
        """Handle paste on textbox with placeholder text."""
        if getattr(textbox, '_is_placeholder', False):
            self._clear_placeholder(textbox)
    
    def _on_textbox_focus_out(self, textbox: ctk.CTkTextbox) -> None:
        """Handle focus out - restore placeholder if empty."""
        content = textbox.get("0.0", "end-1c").strip()
        if not content:
            self._restore_placeholder(textbox)
    
    def _clear_placeholder(self, textbox: ctk.CTkTextbox) -> None:
        """Clear placeholder text and set normal text color."""
        if getattr(textbox, '_is_placeholder', False):
            textbox.delete("0.0", "end")
            textbox.configure(text_color=("gray10", "gray90"))  # Normal text color
            textbox._is_placeholder = False
    
    def _restore_placeholder(self, textbox: ctk.CTkTextbox) -> None:
        """Restore placeholder text if textbox is empty."""
        textbox.delete("0.0", "end")
        textbox.insert("0.0", textbox._placeholder_text)
        textbox.configure(text_color=("gray50", "gray50"))  # Gray color for placeholder
        textbox._is_placeholder = True
    
    def _get_textbox_content(self, textbox: ctk.CTkTextbox) -> str:
        """Get the actual content of textbox, excluding placeholder text."""
        if getattr(textbox, '_is_placeholder', False):
            return ""
        return textbox.get("0.0", "end-1c").strip()

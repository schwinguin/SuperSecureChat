"""
Connection Settings Dialog for the P2P chat application.
Allows users to configure STUN servers and connection parameters.
"""

import customtkinter as ctk
from tkinter import messagebox
import logging
from typing import Optional, Dict, Any, Callable, List

from .security import validate_stun_url, validate_stun_servers, SecurityViolation

logger = logging.getLogger(__name__)


class ConnectionSettingsDialog:
    """
    Dialog for configuring connection settings including STUN servers.
    Allows users to select from predefined STUN servers or add custom ones.
    """
    
    def __init__(self, parent: ctk.CTk, current_settings: Dict[str, Any] = None):
        self.parent = parent
        self.dialog: Optional[ctk.CTkToplevel] = None
        self.current_settings = current_settings or {}
        
        # Current configuration
        self.stun_servers = self.current_settings.get('stun_servers', [
            "stun:stun.l.google.com:19302",
            "stun:stun.stunprotocol.org:3478",
            "stun:stun1.l.google.com:19302",
            "stun:stun2.l.google.com:19302"
        ])
        self.custom_stun_server = self.current_settings.get('custom_stun_server', '')
        self.use_custom_stun = self.current_settings.get('use_custom_stun', False)
        
        # UI elements
        self.predefined_dropdown: Optional[ctk.CTkComboBox] = None
        self.custom_entry: Optional[ctk.CTkEntry] = None
        self.use_custom_checkbox: Optional[ctk.CTkCheckBox] = None
        self.test_button: Optional[ctk.CTkButton] = None
        
        # Callback for when settings are saved
        self.on_settings_saved: Optional[Callable] = None
        
    def show(self):
        """Show the connection settings dialog."""
        self._create_dialog()
        self._setup_ui()
        
    def _create_dialog(self):
        """Create the dialog window."""
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("🌐 Connection Settings")
        self.dialog.geometry("650x600")
        self.dialog.resizable(False, False)
        
        # Make dialog modal - but do it after the window is visible
        self.dialog.transient(self.parent)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (650 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"650x600+{x}+{y}")
        
        # Configure grid
        self.dialog.grid_columnconfigure(0, weight=1)
        self.dialog.grid_rowconfigure(0, weight=1)
        
        # Set grab after the dialog is fully created and positioned
        self.dialog.after(100, self._set_modal)
    
    def _set_modal(self):
        """Set the dialog as modal after it's fully visible."""
        try:
            if self.dialog and self.dialog.winfo_exists():
                self.dialog.grab_set()
                self.dialog.focus_set()
        except Exception as e:
            # If grab_set fails, just continue - dialog will still work
            logger.debug(f"Could not set dialog modal: {e}")
        
    def _setup_ui(self):
        """Set up the dialog UI."""
        # Main container
        main_frame = ctk.CTkFrame(self.dialog, corner_radius=0)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)  # Allow STUN frame to expand
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="🌐 Connection Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(20, 30))
        
        # STUN Server section
        stun_frame = ctk.CTkFrame(main_frame, corner_radius=0)
        stun_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))
        stun_frame.grid_columnconfigure(1, weight=1)
        
        # STUN Server title
        stun_title = ctk.CTkLabel(
            stun_frame,
            text="🔗 STUN Server Configuration",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        stun_title.grid(row=0, column=0, columnspan=2, pady=(15, 10))
        
        # Info text
        info_text = ctk.CTkLabel(
            stun_frame,
            text="STUN servers help establish peer-to-peer connections through NAT/firewalls.\nChoose a predefined server or enter your own for better privacy.",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            justify="left"
        )
        info_text.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="w")
        
        # Predefined STUN servers
        predefined_label = ctk.CTkLabel(
            stun_frame,
            text="📋 Predefined Servers:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        predefined_label.grid(row=2, column=0, padx=15, pady=(0, 5), sticky="w")
        
        predefined_servers = [
            "stun:stun.l.google.com:19302 (Google - Default)",
            "stun:stun.stunprotocol.org:3478 (STUN Protocol)",
            "stun:stun1.l.google.com:19302 (Google Alternative 1)",
            "stun:stun2.l.google.com:19302 (Google Alternative 2)"
        ]
        
        self.predefined_dropdown = ctk.CTkComboBox(
            stun_frame,
            values=predefined_servers,
            state="readonly",
            width=400,
            command=self._on_predefined_selected
        )
        self.predefined_dropdown.grid(row=3, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")
        
        # Set current selection
        current_stun = self.stun_servers[0] if self.stun_servers else "stun:stun.l.google.com:19302"
        for i, server_desc in enumerate(predefined_servers):
            if current_stun in server_desc:
                self.predefined_dropdown.set(server_desc)
                break
        
        # Custom STUN server section
        custom_label = ctk.CTkLabel(
            stun_frame,
            text="🔧 Custom STUN Server:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        custom_label.grid(row=4, column=0, padx=15, pady=(15, 5), sticky="w")
        
        # Custom checkbox
        self.use_custom_checkbox = ctk.CTkCheckBox(
            stun_frame,
            text="Use custom STUN server",
            command=self._on_custom_checkbox_changed
        )
        self.use_custom_checkbox.grid(row=5, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="w")
        
        if self.use_custom_stun:
            self.use_custom_checkbox.select()
        
        # Custom entry
        self.custom_entry = ctk.CTkEntry(
            stun_frame,
            placeholder_text="stun:your-stun-server.com:3478",
            width=400
        )
        self.custom_entry.grid(row=6, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")
        
        if self.custom_stun_server:
            self.custom_entry.insert(0, self.custom_stun_server)
        
        # Update entry state based on checkbox
        self._on_custom_checkbox_changed()
        
        # Test button
        self.test_button = ctk.CTkButton(
            stun_frame,
            text="🧪 Test Connection",
            command=self._test_stun_server,
            width=150,
            corner_radius=8
        )
        self.test_button.grid(row=7, column=0, columnspan=2, pady=(0, 20))
        
        # Buttons frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, pady=(30, 20), sticky="ew")
        
        # Cancel button
        cancel_button = ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            command=self._cancel,
            corner_radius=8,
            width=120,
            fg_color=("gray60", "gray40"),
            hover_color=("gray50", "gray30")
        )
        cancel_button.grid(row=0, column=0, padx=(0, 10))
        
        # Save button
        save_button = ctk.CTkButton(
            button_frame,
            text="💾 Save Settings",
            command=self._save_settings,
            corner_radius=8,
            width=120
        )
        save_button.grid(row=0, column=1, padx=(10, 0))
        
    def _on_predefined_selected(self, selection: str):
        """Handle predefined server selection."""
        # Uncheck custom if predefined is selected
        if self.use_custom_checkbox.get():
            self.use_custom_checkbox.deselect()
            self._on_custom_checkbox_changed()
    
    def _on_custom_checkbox_changed(self):
        """Handle custom checkbox state change."""
        use_custom = self.use_custom_checkbox.get()
        
        # Enable/disable custom entry
        if use_custom:
            self.custom_entry.configure(state="normal")
            self.predefined_dropdown.configure(state="disabled")
        else:
            self.custom_entry.configure(state="disabled")
            self.predefined_dropdown.configure(state="readonly")
    
    def _test_stun_server(self):
        """Test the selected STUN server configuration."""
        try:
            stun_url = self._get_selected_stun_url()
            if not stun_url:
                messagebox.showerror("Error", "Please select or enter a STUN server URL")
                return
            
            # Validate the STUN URL
            validated_url = validate_stun_url(stun_url)
            
            # For now, just show success if validation passes
            # In a full implementation, you might want to actually test connectivity
            messagebox.showinfo(
                "Test Result", 
                f"✅ STUN server URL is valid:\n{validated_url}\n\n"
                "Note: This validates the URL format. Actual connectivity "
                "will be tested when establishing a connection."
            )
            
        except SecurityViolation as e:
            messagebox.showerror("Validation Error", f"Invalid STUN server URL:\n{e}")
        except Exception as e:
            logger.error(f"Error testing STUN server: {e}")
            messagebox.showerror("Error", f"Failed to test STUN server:\n{e}")
    
    def _get_selected_stun_url(self) -> str:
        """Get the currently selected STUN server URL."""
        if self.use_custom_checkbox.get():
            return self.custom_entry.get().strip()
        else:
            selection = self.predefined_dropdown.get()
            # Extract URL from description
            if "stun.l.google.com:19302" in selection:
                return "stun:stun.l.google.com:19302"
            elif "stun.stunprotocol.org:3478" in selection:
                return "stun:stun.stunprotocol.org:3478"
            elif "stun1.l.google.com:19302" in selection:
                return "stun:stun1.l.google.com:19302"
            elif "stun2.l.google.com:19302" in selection:
                return "stun:stun2.l.google.com:19302"
            return "stun:stun.l.google.com:19302"  # Default
    
    def _save_settings(self):
        """Save the connection settings."""
        try:
            use_custom = self.use_custom_checkbox.get()
            
            if use_custom:
                custom_url = self.custom_entry.get().strip()
                if not custom_url:
                    messagebox.showerror("Error", "Please enter a custom STUN server URL")
                    return
                
                # Validate custom URL
                validated_url = validate_stun_url(custom_url)
                stun_servers = [validated_url]
                custom_stun_server = validated_url
            else:
                selected_url = self._get_selected_stun_url()
                stun_servers = [selected_url]
                custom_stun_server = ""
            
            # Create settings dictionary
            settings = {
                'stun_servers': stun_servers,
                'custom_stun_server': custom_stun_server,
                'use_custom_stun': use_custom
            }
            
            # Call callback if set
            if self.on_settings_saved:
                self.on_settings_saved(settings)
            
            # Close dialog
            self._close_dialog()
            
        except SecurityViolation as e:
            messagebox.showerror("Validation Error", f"Invalid settings:\n{e}")
        except Exception as e:
            logger.error(f"Error saving connection settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings:\n{e}")
    
    def _cancel(self):
        """Cancel and close the dialog."""
        self._close_dialog()
    
    def _close_dialog(self):
        """Close the dialog window."""
        if self.dialog:
            try:
                self.dialog.grab_release()
            except Exception:
                # Ignore grab_release errors
                pass
            try:
                self.dialog.destroy()
            except Exception:
                # Ignore destroy errors
                pass
            self.dialog = None

"""
Modern GUI module for the P2P chat application.
Contains theme setup and imports all GUI components.
"""

import customtkinter as ctk

# Set appearance mode and default color theme
ctk.set_appearance_mode("dark")  # "system", "dark", "light"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

# Import all GUI components
from .file_transfer_dialog import FileTransferDialog
from .file_progress_dialog import FileProgressDialog
from .modern_chat_window import ModernChatWindow
from .chat_window import ChatWindow
from .audio_settings_dialog import AudioSettingsDialog

# Make all classes available at module level for backward compatibility
__all__ = [
    'FileTransferDialog',
    'FileProgressDialog', 
    'ModernChatWindow',
    'ChatWindow',
    'AudioSettingsDialog'
] 
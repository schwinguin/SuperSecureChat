"""
Compatibility wrapper for the P2P chat application.
Provides backward compatibility with the original ChatWindow interface.
"""

import customtkinter as ctk
from .modern_chat_window import ModernChatWindow


class ChatWindow(ModernChatWindow):
    """Compatibility wrapper for the original ChatWindow interface."""
    
    def __init__(self, root):
        # Convert Tk root to CTk if needed
        if isinstance(root, ctk.CTk):
            super().__init__(root)
        else:
            # This shouldn't happen in normal usage, but provides fallback
            modern_root = ctk.CTk()
            modern_root.title(root.title())
            modern_root.geometry(root.geometry())
            root.destroy()
            super().__init__(modern_root) 
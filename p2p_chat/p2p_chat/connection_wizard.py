"""
Connection Wizard for the P2P chat application.
Provides a step-by-step guided interface for creating and joining chats.
"""

import customtkinter as ctk
from tkinter import messagebox
import logging
from typing import Optional, Callable, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class WizardStep(Enum):
    """Enumeration of wizard steps."""
    WELCOME = "welcome"
    USERNAME = "username"
    CONNECTION_TYPE = "connection_type"
    CREATE_CHAT = "create_chat"
    SHARE_INVITE = "share_invite"
    WAIT_FOR_RETURN = "wait_for_return"
    JOIN_CHAT = "join_chat"
    SHARE_RETURN = "share_return"
    WAITING_CONNECTION = "waiting_connection"


class ConnectionWizard:
    """
    Step-by-step connection wizard for P2P chat.
    
    Provides a guided interface that walks users through:
    1. Welcome screen with app info
    2. Username entry
    3. Connection type selection (Create/Join)
    4. Create chat flow with invite key
    5. Join chat flow with invite key entry
    6. Connection status and waiting
    """
    
    def __init__(self, parent: ctk.CTk):
        self.parent = parent
        self.wizard_frame: Optional[ctk.CTkFrame] = None
        self.current_step = WizardStep.WELCOME
        self.step_history = []
        
        # Wizard data
        self.username = "Anonymous"
        self.connection_type = None  # "create" or "join"
        self.invite_key = ""
        self.return_key = ""
        
        # UI elements
        self.content_frame: Optional[ctk.CTkFrame] = None
        self.navigation_frame: Optional[ctk.CTkFrame] = None
        self.progress_frame: Optional[ctk.CTkFrame] = None
        self.step_indicators = []
        
        # Callbacks
        self.on_create_chat: Optional[Callable] = None
        self.on_join_chat: Optional[Callable] = None
        self.on_connect_chat: Optional[Callable] = None
        self.on_wizard_complete: Optional[Callable] = None
        self.on_wizard_cancel: Optional[Callable] = None
        
        # UI state
        self.current_content = None
        
    def show(self) -> None:
        """Show the connection wizard."""
        self._create_wizard_frame()
        self._setup_ui()
        self._show_step(WizardStep.WELCOME)
    
    def _create_wizard_frame(self) -> None:
        """Create the main wizard frame."""
        # Use the parent directly instead of creating a nested frame
        self.wizard_frame = self.parent
        # Configure the parent frame for wizard layout
        self.wizard_frame.grid_columnconfigure(0, weight=1)
        self.wizard_frame.grid_rowconfigure(2, weight=1)  # Content area
        
    def _setup_ui(self) -> None:
        """Set up the wizard UI structure."""
        # Header with title and progress
        self._setup_header()
        
        # Content area - create a separate frame for wizard content
        self.content_frame = ctk.CTkFrame(self.wizard_frame, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Navigation area
        self._setup_navigation()
    
    def _setup_header(self) -> None:
        """Set up the wizard header with title and progress indicators."""
        # Title
        title_label = ctk.CTkLabel(
            self.wizard_frame,
            text="🔒 P2P Secure Chat - Connection Wizard",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, pady=(10, 8), padx=20)
        
        # Progress indicators
        self.progress_frame = ctk.CTkFrame(self.wizard_frame, fg_color="transparent")
        self.progress_frame.grid(row=1, column=0, pady=(0, 8), padx=20)
        
        self._update_progress_indicators()
    
    def _setup_navigation(self) -> None:
        """Set up the navigation buttons."""
        self.navigation_frame = ctk.CTkFrame(self.wizard_frame, fg_color="transparent")
        self.navigation_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(5, 10))
        self.navigation_frame.grid_columnconfigure(0, weight=1)
        self.navigation_frame.grid_columnconfigure(1, weight=0)
        
        # Back button (initially hidden)
        self.back_btn = ctk.CTkButton(
            self.navigation_frame,
            text="← Back",
            width=100,
            height=35,
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            command=self._go_back,
            fg_color=("gray60", "gray40"),
            hover_color=("gray50", "gray50")
        )
        self.back_btn.grid(row=0, column=0, sticky="w")
        
        
        # Next/Complete button (initially hidden)
        self.next_btn = ctk.CTkButton(
            self.navigation_frame,
            text="Next →",
            width=100,
            height=35,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=8,
            command=self._go_next,
            fg_color=("gray50", "gray30"),
            hover_color=("gray60", "gray20")
        )
        self.next_btn.grid(row=0, column=1, sticky="e", padx=(0, 10))
    
    def _update_progress_indicators(self) -> None:
        """Update the progress step indicators."""
        # Clear existing indicators
        for indicator in self.step_indicators:
            indicator.destroy()
        self.step_indicators.clear()
        
        # Define steps and their positions
        if self.connection_type == "create":
            steps = [
                ("Welcome", WizardStep.WELCOME),
                ("Username", WizardStep.USERNAME),
                ("Type", WizardStep.CONNECTION_TYPE),
                ("Create", WizardStep.CREATE_CHAT),
                ("Share", WizardStep.SHARE_INVITE),
                ("Wait", WizardStep.WAIT_FOR_RETURN),
                ("Connect", WizardStep.WAITING_CONNECTION)
            ]
        elif self.connection_type == "join":
            steps = [
                ("Welcome", WizardStep.WELCOME),
                ("Username", WizardStep.USERNAME),
                ("Type", WizardStep.CONNECTION_TYPE),
                ("Join", WizardStep.JOIN_CHAT),
                ("Share", WizardStep.SHARE_RETURN),
                ("Connect", WizardStep.WAITING_CONNECTION)
            ]
        else:
            steps = [
                ("Welcome", WizardStep.WELCOME),
                ("Username", WizardStep.USERNAME),
                ("Type", WizardStep.CONNECTION_TYPE)
            ]
        
        # Create step indicators
        for i, (step_name, step_enum) in enumerate(steps):
            # Skip connection step if not yet determined
            if step_enum in [WizardStep.CREATE_CHAT, WizardStep.JOIN_CHAT] and not self.connection_type:
                continue
                
            # Determine if this step is current, completed, or pending
            if step_enum == self.current_step:
                color = ("#4A90E2", "#4A90E2")  # Blue for current
                text_color = ("white", "white")
            elif self._is_step_completed(step_enum):
                color = ("#5CB85C", "#5CB85C")  # Green for completed
                text_color = ("white", "white")
            else:
                color = ("gray70", "gray30")  # Gray for pending
                text_color = ("gray50", "gray50")
            
            # Create step indicator
            step_frame = ctk.CTkFrame(self.progress_frame, corner_radius=0, fg_color=color)
            step_frame.grid(row=0, column=i, padx=5)
            
            step_label = ctk.CTkLabel(
                step_frame,
                text=step_name,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=text_color
            )
            step_label.grid(row=0, column=0, padx=15, pady=8)
            
            self.step_indicators.append(step_frame)
    
    def _is_step_completed(self, step: WizardStep) -> bool:
        """Check if a step has been completed."""
        if step == WizardStep.WELCOME:
            return self.current_step != WizardStep.WELCOME
        elif step == WizardStep.USERNAME:
            return self.username != "Anonymous" or self.current_step in [WizardStep.CONNECTION_TYPE, WizardStep.CREATE_CHAT, WizardStep.SHARE_INVITE, WizardStep.WAIT_FOR_RETURN, WizardStep.JOIN_CHAT, WizardStep.SHARE_RETURN, WizardStep.WAITING_CONNECTION]
        elif step == WizardStep.CONNECTION_TYPE:
            return self.connection_type is not None
        elif step == WizardStep.CREATE_CHAT:
            return self.current_step in [WizardStep.SHARE_INVITE, WizardStep.WAIT_FOR_RETURN, WizardStep.WAITING_CONNECTION]
        elif step == WizardStep.SHARE_INVITE:
            return self.current_step in [WizardStep.WAIT_FOR_RETURN, WizardStep.WAITING_CONNECTION]
        elif step == WizardStep.WAIT_FOR_RETURN:
            return self.current_step == WizardStep.WAITING_CONNECTION
        elif step == WizardStep.JOIN_CHAT:
            return self.current_step in [WizardStep.SHARE_RETURN, WizardStep.WAITING_CONNECTION]
        elif step == WizardStep.SHARE_RETURN:
            return self.current_step == WizardStep.WAITING_CONNECTION
        elif step == WizardStep.WAITING_CONNECTION:
            return False  # This step is never "completed" as it's the final step
        return False
    
    def _show_step(self, step: WizardStep) -> None:
        """Show a specific wizard step."""
        # Clear current content
        if self.current_content:
            self.current_content.destroy()
            self.current_content = None
        
        # Add to history
        if not self.step_history or self.step_history[-1] != step:
            self.step_history.append(step)
        
        self.current_step = step
        
        # Show step content
        if step == WizardStep.WELCOME:
            self._show_welcome_step()
        elif step == WizardStep.USERNAME:
            self._show_username_step()
        elif step == WizardStep.CONNECTION_TYPE:
            self._show_connection_type_step()
        elif step == WizardStep.CREATE_CHAT:
            self._show_create_chat_step()
        elif step == WizardStep.SHARE_INVITE:
            self._show_share_invite_step()
        elif step == WizardStep.WAIT_FOR_RETURN:
            self._show_wait_for_return_step()
        elif step == WizardStep.JOIN_CHAT:
            self._show_join_chat_step()
        elif step == WizardStep.SHARE_RETURN:
            self._show_share_return_step()
        elif step == WizardStep.WAITING_CONNECTION:
            self._show_waiting_connection_step()
        
        # Update navigation
        self._update_navigation()
        self._update_progress_indicators()
    
    def _show_welcome_step(self) -> None:
        """Show the welcome step."""
        self.current_content = ctk.CTkFrame(self.content_frame, corner_radius=0)
        self.current_content.grid(row=0, column=0, sticky="nsew", padx=20, pady=5)
        self.current_content.grid_columnconfigure(0, weight=1)
        
        # Welcome content
        welcome_label = ctk.CTkLabel(
            self.current_content,
            text="Welcome to P2P Secure Chat!",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("gray10", "gray90")
        )
        welcome_label.grid(row=0, column=0, pady=(20, 10))
        
        # Features list
        features_text = ctk.CTkLabel(
            self.current_content,
            text="🔒 End-to-end encrypted messaging\n"
                 "🌐 Direct peer-to-peer connection\n"
                 "📁 Secure file transfers\n"
                 "🎤 Real-time voice chat\n"
                 "🚫 No servers - complete privacy",
            font=ctk.CTkFont(size=14),
            text_color=("gray40", "gray60"),
            justify="left"
        )
        features_text.grid(row=1, column=0, pady=(0, 15))
        
        # Instructions
        instructions_label = ctk.CTkLabel(
            self.current_content,
            text="This wizard will guide you through setting up a secure connection.\n"
                 "You can either create a new chat room or join an existing one.",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray50"),
            justify="center"
        )
        instructions_label.grid(row=2, column=0, pady=(0, 20))
    
    def _show_username_step(self) -> None:
        """Show the username entry step."""
        self.current_content = ctk.CTkFrame(self.content_frame, corner_radius=0)
        self.current_content.grid(row=0, column=0, sticky="nsew", padx=20, pady=5)
        self.current_content.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.current_content,
            text="👤 Choose Your Display Name",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, pady=(20, 10))
        
        # Instructions
        instructions_label = ctk.CTkLabel(
            self.current_content,
            text="Enter a name that will be displayed to other participants.\n"
                 "This can be changed later in the chat settings.",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            justify="center"
        )
        instructions_label.grid(row=1, column=0, pady=(0, 15))
        
        # Username entry
        self.username_entry = ctk.CTkEntry(
            self.current_content,
            placeholder_text="Enter your display name (optional)",
            font=ctk.CTkFont(size=14),
            height=40,
            corner_radius=8,
            width=400
        )
        self.username_entry.grid(row=2, column=0, pady=(0, 10))
        
        # Set current username if available
        if self.username != "Anonymous":
            self.username_entry.insert(0, self.username)
        
        # Note
        note_label = ctk.CTkLabel(
            self.current_content,
            text="💡 Leave empty to use 'Anonymous'",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray50")
        )
        note_label.grid(row=3, column=0, pady=(0, 20))
    
    
    def _show_connection_type_step(self) -> None:
        """Show the connection type selection step."""
        self.current_content = ctk.CTkFrame(self.content_frame, corner_radius=0)
        self.current_content.grid(row=0, column=0, sticky="nsew", padx=20, pady=5)
        self.current_content.grid_columnconfigure(0, weight=1)
        self.current_content.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.current_content,
            text="🔗 Choose Connection Type",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(20, 15))
        
        # Create chat option
        create_frame = ctk.CTkFrame(self.current_content, corner_radius=0)
        create_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        create_frame.grid_columnconfigure(0, weight=1)
        
        create_icon = ctk.CTkLabel(
            create_frame,
            text="🚀",
            font=ctk.CTkFont(size=36)
        )
        create_icon.grid(row=0, column=0, pady=(15, 5))
        
        create_title = ctk.CTkLabel(
            create_frame,
            text="Create New Chat",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray10", "gray90")
        )
        create_title.grid(row=1, column=0, pady=(0, 5))
        
        create_desc = ctk.CTkLabel(
            create_frame,
            text="Start a new secure chat room\nand invite others to join",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            justify="center"
        )
        create_desc.grid(row=2, column=0, pady=(0, 10))
        
        self.create_btn = ctk.CTkButton(
            create_frame,
            text="Create Chat",
            width=150,
            height=35,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=8,
            command=lambda: self._select_connection_type("create"),
            fg_color=("gray50", "gray30"),
            hover_color=("gray60", "gray20")
        )
        self.create_btn.grid(row=3, column=0, pady=(0, 15))
        
        # Join chat option
        join_frame = ctk.CTkFrame(self.current_content, corner_radius=0)
        join_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
        join_frame.grid_columnconfigure(0, weight=1)
        
        join_icon = ctk.CTkLabel(
            join_frame,
            text="🔗",
            font=ctk.CTkFont(size=36)
        )
        join_icon.grid(row=0, column=0, pady=(15, 5))
        
        join_title = ctk.CTkLabel(
            join_frame,
            text="Join Existing Chat",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray10", "gray90")
        )
        join_title.grid(row=1, column=0, pady=(0, 5))
        
        join_desc = ctk.CTkLabel(
            join_frame,
            text="Connect to an existing\nchat room using an invite key",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            justify="center"
        )
        join_desc.grid(row=2, column=0, pady=(0, 10))
        
        self.join_btn = ctk.CTkButton(
            join_frame,
            text="Join Chat",
            width=150,
            height=35,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=8,
            command=lambda: self._select_connection_type("join"),
            fg_color=("gray50", "gray30"),
            hover_color=("gray60", "gray20")
        )
        self.join_btn.grid(row=3, column=0, pady=(0, 15))
    
    def _show_create_chat_step(self) -> None:
        """Show the create chat step - just shows that chat is being created."""
        self.current_content = ctk.CTkFrame(self.content_frame, corner_radius=0)
        self.current_content.grid(row=0, column=0, sticky="nsew", padx=20, pady=5)
        self.current_content.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.current_content,
            text="🚀 Creating Your Chat Room",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, pady=(20, 10))
        
        # Instructions
        instructions_label = ctk.CTkLabel(
            self.current_content,
            text="Your secure chat room is being created...\n"
                 "You'll be able to share your invite key in the next step.",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            justify="center"
        )
        instructions_label.grid(row=1, column=0, pady=(0, 15))
        
        # Progress indicator
        self.progress_bar = ctk.CTkProgressBar(
            self.current_content,
            width=300,
            height=20,
            corner_radius=0
        )
        self.progress_bar.grid(row=2, column=0, pady=(0, 15))
        self.progress_bar.set(0.5)  # Indeterminate progress
        
        # Continue button (will be shown when invite key is ready)
        self.continue_btn = ctk.CTkButton(
            self.current_content,
            text="📤 Share Invite Key →",
            width=200,
            height=35,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=8,
            command=lambda: self._show_step(WizardStep.SHARE_INVITE),
            fg_color=("gray50", "gray30"),
            hover_color=("gray60", "gray20")
        )
        self.continue_btn.grid(row=3, column=0, pady=(0, 20))
    
    def _show_join_chat_step(self) -> None:
        """Show the join chat step."""
        self.current_content = ctk.CTkScrollableFrame(self.content_frame, corner_radius=0)
        self.current_content.grid(row=0, column=0, sticky="nsew", padx=20, pady=5)
        self.current_content.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.current_content,
            text="🔗 Joining a Chat Room",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, pady=(15, 5))
        
        # Instructions
        instructions_label = ctk.CTkLabel(
            self.current_content,
            text="Paste the invite key you received from the chat creator below.\n"
                 "You'll then receive a return key to share back with them.",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            justify="left"
        )
        instructions_label.grid(row=1, column=0, pady=(0, 10))
        
        # Invite key input section
        invite_label = ctk.CTkLabel(
            self.current_content,
            text="📨 Invite Key",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray30", "gray70")
        )
        invite_label.grid(row=2, column=0, pady=(10, 5))
        
        self.join_entry = ctk.CTkTextbox(
            self.current_content,
            height=100,
            font=ctk.CTkFont(size=12, family="monospace"),
            corner_radius=0
        )
        self.join_entry.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 5))
        
        # Set up placeholder text
        self.join_entry_placeholder = "Paste the invite key here..."
        self._setup_placeholder_text(self.join_entry, self.join_entry_placeholder)
        
        # Join button
        self.join_submit_btn = ctk.CTkButton(
            self.current_content,
            text="🚀 Join Chat",
            width=160,
            height=35,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=8,
            command=self._on_join_with_key,
            fg_color=("gray50", "gray30"),
            hover_color=("gray60", "gray20")
        )
        self.join_submit_btn.grid(row=4, column=0, pady=(0, 10))
        
        # Return key display section (initially hidden)
        self.return_display_frame = ctk.CTkFrame(self.current_content, corner_radius=0)
        self.return_display_frame.grid_columnconfigure(0, weight=1)
        
        return_display_label = ctk.CTkLabel(
            self.return_display_frame,
            text="📤 Your Return Key (Share This Back)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray30", "gray70")
        )
        return_display_label.grid(row=0, column=0, pady=(10, 5))
        
        self.return_display_text = ctk.CTkTextbox(
            self.return_display_frame,
            height=100,
            font=ctk.CTkFont(size=12, family="monospace"),
            corner_radius=8,
            state="disabled"
        )
        self.return_display_text.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 5))
        
        self.copy_return_btn = ctk.CTkButton(
            self.return_display_frame,
            text="📋 Copy Return Key",
            width=160,
            height=35,
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            command=self._copy_return_key,
            fg_color=("gray45", "gray35"),
            hover_color=("gray55", "gray25")
        )
        self.copy_return_btn.grid(row=2, column=0, pady=(0, 10))
    
    def _show_share_invite_step(self) -> None:
        """Show the share invite key step."""
        self.current_content = ctk.CTkFrame(self.content_frame, corner_radius=0)
        self.current_content.grid(row=0, column=0, sticky="nsew", padx=20, pady=5)
        self.current_content.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.current_content,
            text="📤 Share Your Invite Key",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, pady=(20, 10))
        
        # Instructions
        instructions_label = ctk.CTkLabel(
            self.current_content,
            text="Copy and share this invite key with the person you want to chat with.\n"
                 "They will need to enter it in their app to join your chat.",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            justify="center"
        )
        instructions_label.grid(row=1, column=0, pady=(0, 15))
        
        # Invite key display
        invite_label = ctk.CTkLabel(
            self.current_content,
            text="📤 Your Invite Key",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray30", "gray70")
        )
        invite_label.grid(row=2, column=0, pady=(10, 5))
        
        self.invite_text = ctk.CTkTextbox(
            self.current_content,
            height=100,
            font=ctk.CTkFont(size=12, family="monospace"),
            corner_radius=8,
            state="disabled"
        )
        self.invite_text.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 5))
        
        self.copy_invite_btn = ctk.CTkButton(
            self.current_content,
            text="📋 Copy to Clipboard",
            width=160,
            height=35,
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            command=self._copy_invite_key,
            fg_color=("gray45", "gray35"),
            hover_color=("gray55", "gray25")
        )
        self.copy_invite_btn.grid(row=4, column=0, pady=(0, 10))
        
        # Next step button
        self.next_step_btn = ctk.CTkButton(
            self.current_content,
            text="⏳ Wait for Return Key →",
            width=200,
            height=35,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=8,
            command=lambda: self._show_step(WizardStep.WAIT_FOR_RETURN),
            fg_color=("gray50", "gray30"),
            hover_color=("gray60", "gray20")
        )
        self.next_step_btn.grid(row=5, column=0, pady=(0, 20))
    
    def _show_wait_for_return_step(self) -> None:
        """Show the wait for return key step."""
        self.current_content = ctk.CTkFrame(self.content_frame, corner_radius=0)
        self.current_content.grid(row=0, column=0, sticky="nsew", padx=20, pady=5)
        self.current_content.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.current_content,
            text="⏳ Waiting for Return Key",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, pady=(20, 10))
        
        # Instructions
        instructions_label = ctk.CTkLabel(
            self.current_content,
            text="Wait for your peer to send you their return key.\n"
                 "Once you receive it, paste it below to establish the connection.",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            justify="center"
        )
        instructions_label.grid(row=1, column=0, pady=(0, 15))
        
        # Return key input
        return_label = ctk.CTkLabel(
            self.current_content,
            text="📥 Return Key (Paste Here)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray30", "gray70")
        )
        return_label.grid(row=2, column=0, pady=(10, 5))
        
        self.return_entry = ctk.CTkTextbox(
            self.current_content,
            height=100,
            font=ctk.CTkFont(size=12, family="monospace"),
            corner_radius=0
        )
        self.return_entry.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 5))
        
        # Set up placeholder text
        self.return_entry_placeholder = "Paste the return key from your peer here..."
        self._setup_placeholder_text(self.return_entry, self.return_entry_placeholder)
        
        # Connect button
        self.connect_btn = ctk.CTkButton(
            self.current_content,
            text="🔗 Connect Now",
            width=160,
            height=35,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=8,
            command=self._on_connect,
            fg_color=("gray50", "gray30"),
            hover_color=("gray60", "gray20")
        )
        self.connect_btn.grid(row=4, column=0, pady=(0, 20))
    
    def _show_share_return_step(self) -> None:
        """Show the share return key step."""
        self.current_content = ctk.CTkFrame(self.content_frame, corner_radius=0)
        self.current_content.grid(row=0, column=0, sticky="nsew", padx=20, pady=5)
        self.current_content.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.current_content,
            text="📤 Share Your Return Key",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, pady=(20, 10))
        
        # Instructions
        instructions_label = ctk.CTkLabel(
            self.current_content,
            text="Copy and share this return key with the chat creator.\n"
                 "They will use it to complete the connection.",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            justify="center"
        )
        instructions_label.grid(row=1, column=0, pady=(0, 15))
        
        # Return key display
        return_label = ctk.CTkLabel(
            self.current_content,
            text="📤 Your Return Key",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray30", "gray70")
        )
        return_label.grid(row=2, column=0, pady=(10, 5))
        
        self.return_display_text = ctk.CTkTextbox(
            self.current_content,
            height=100,
            font=ctk.CTkFont(size=12, family="monospace"),
            corner_radius=8,
            state="disabled"
        )
        self.return_display_text.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 5))
        
        self.copy_return_btn = ctk.CTkButton(
            self.current_content,
            text="📋 Copy to Clipboard",
            width=160,
            height=35,
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            command=self._copy_return_key,
            fg_color=("gray45", "gray35"),
            hover_color=("gray55", "gray25")
        )
        self.copy_return_btn.grid(row=4, column=0, pady=(0, 10))
        
        # Waiting message
        waiting_label = ctk.CTkLabel(
            self.current_content,
            text="⏳ Waiting for connection...",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray50")
        )
        waiting_label.grid(row=5, column=0, pady=(0, 20))
    
    def _show_waiting_connection_step(self) -> None:
        """Show the waiting for connection step."""
        self.current_content = ctk.CTkFrame(self.content_frame, corner_radius=0)
        self.current_content.grid(row=0, column=0, sticky="nsew", padx=20, pady=5)
        self.current_content.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.current_content,
            text="⏳ Establishing Connection",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, pady=(20, 10))
        
        # Status message (removed - using main status bar instead)
        status_text = ctk.CTkLabel(
            self.current_content,
            text="Waiting for peer connection...",
            font=ctk.CTkFont(size=14),
            text_color=("gray40", "gray60")
        )
        status_text.grid(row=1, column=0, pady=(0, 15))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.current_content,
            width=300,
            height=20,
            corner_radius=0
        )
        self.progress_bar.grid(row=2, column=0, pady=(0, 15))
        self.progress_bar.set(0.5)  # Indeterminate progress
        
        # Instructions
        instructions_label = ctk.CTkLabel(
            self.current_content,
            text="Please wait while we establish a secure connection.\n"
                 "This may take a few moments depending on your network.",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray50"),
            justify="center"
        )
        instructions_label.grid(row=3, column=0, pady=(0, 20))
    
    def _update_navigation(self) -> None:
        """Update navigation buttons based on current step."""
        # Show/hide back button
        if len(self.step_history) > 1:
            self.back_btn.grid()
        else:
            self.back_btn.grid_remove()
        
        # Update next button text and visibility
        if self.current_step == WizardStep.WELCOME:
            self.next_btn.configure(text="Start chatting")
            self.next_btn.grid()
        elif self.current_step == WizardStep.USERNAME:
            self.next_btn.configure(text="Continue →")
            self.next_btn.grid()
        elif self.current_step == WizardStep.CONNECTION_TYPE:
            self.next_btn.grid_remove()  # Hide next button, use individual action buttons
        elif self.current_step in [WizardStep.CREATE_CHAT, WizardStep.SHARE_INVITE, WizardStep.WAIT_FOR_RETURN, WizardStep.JOIN_CHAT, WizardStep.SHARE_RETURN]:
            self.next_btn.grid_remove()  # Hide next button, use specific action buttons
        elif self.current_step == WizardStep.WAITING_CONNECTION:
            self.next_btn.grid_remove()  # Hide next button during connection
    
    def _go_next(self) -> None:
        """Go to the next step."""
        if self.current_step == WizardStep.WELCOME:
            self._show_step(WizardStep.USERNAME)
        elif self.current_step == WizardStep.USERNAME:
            self._save_username()
            self._show_step(WizardStep.CONNECTION_TYPE)
    
    def _go_back(self) -> None:
        """Go back to the previous step."""
        if len(self.step_history) > 1:
            # Remove current step from history
            self.step_history.pop()
            # Go to previous step
            previous_step = self.step_history[-1]
            self._show_step(previous_step)
    
    def _select_connection_type(self, connection_type: str) -> None:
        """Select connection type and proceed."""
        self.connection_type = connection_type
        self._save_username()
        
        if connection_type == "create":
            self._show_step(WizardStep.CREATE_CHAT)
            # Trigger create chat
            if self.on_create_chat:
                self.on_create_chat()
        elif connection_type == "join":
            self._show_step(WizardStep.JOIN_CHAT)
    
    def _save_username(self) -> None:
        """Save the current username."""
        if hasattr(self, 'username_entry') and self.username_entry and self.username_entry.winfo_exists():
            try:
                username = self.username_entry.get().strip()
                self.username = username if username else "Anonymous"
            except Exception as e:
                # Widget may have been destroyed, use current username
                logger.debug(f"Could not get username from entry: {e}")
                pass
    
    def _on_join_with_key(self) -> None:
        """Handle join with key submission."""
        if hasattr(self, 'join_entry') and self.join_entry and self.join_entry.winfo_exists():
            invite_key = self._get_textbox_content(self.join_entry)
            if invite_key and self.on_join_chat:
                self.on_join_chat(invite_key)
            else:
                messagebox.showwarning("Invalid Input", "Please enter a valid invite key.")
        else:
            messagebox.showerror("Error", "Join input field not found!")
    
    def _on_connect(self) -> None:
        """Handle connect button click."""
        if hasattr(self, 'return_entry') and self.return_entry and self.return_entry.winfo_exists():
            return_key = self._get_textbox_content(self.return_entry)
            if return_key and self.on_connect_chat:
                self.on_connect_chat(return_key)
                self._show_step(WizardStep.WAITING_CONNECTION)
            else:
                messagebox.showwarning("Invalid Input", "Please enter a valid return key.")
        else:
            messagebox.showerror("Error", "Return key input field not found!")
    
    def _copy_invite_key(self) -> None:
        """Copy invite key to clipboard."""
        if self.invite_key:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(self.invite_key)
            # Show temporary feedback
            original_text = self.copy_invite_btn.cget("text")
            self.copy_invite_btn.configure(text="✅ Copied!")
            self.parent.after(2000, lambda: self.copy_invite_btn.configure(text=original_text))
    
    def _copy_return_key(self) -> None:
        """Copy return key to clipboard."""
        if self.return_key:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(self.return_key)
            # Show temporary feedback
            if hasattr(self, 'copy_return_btn'):
                original_text = self.copy_return_btn.cget("text")
                self.copy_return_btn.configure(text="✅ Copied!")
                self.parent.after(2000, lambda: self.copy_return_btn.configure(text=original_text))
    
    
    def hide(self) -> None:
        """Hide the wizard."""
        # Clear all wizard content from the parent frame
        if self.wizard_frame:
            # Clear all children of the wizard frame
            for child in self.wizard_frame.winfo_children():
                child.destroy()
            # Don't set wizard_frame to None to avoid destroying the parent
            # self.wizard_frame = None
    
    # Public interface methods
    
    def set_invite_key(self, invite_key: str) -> None:
        """Set the invite key and move to share invite step."""
        self.invite_key = invite_key
        # Move to share invite step
        self._show_step(WizardStep.SHARE_INVITE)
        if hasattr(self, 'invite_text') and self.invite_text and self.invite_text.winfo_exists():
            self.invite_text.configure(state="normal")
            self.invite_text.delete("0.0", "end")
            self.invite_text.insert("0.0", invite_key)
            self.invite_text.configure(state="disabled")
    
    def set_return_key(self, return_key: str) -> None:
        """Set the return key and move to share return step."""
        self.return_key = return_key
        # Move to share return step
        self._show_step(WizardStep.SHARE_RETURN)
        if hasattr(self, 'return_display_text') and self.return_display_text and self.return_display_text.winfo_exists():
            self.return_display_text.configure(state="normal")
            self.return_display_text.delete("0.0", "end")
            self.return_display_text.insert("0.0", return_key)
            self.return_display_text.configure(state="disabled")
    
    def set_connection_status(self, status: str, color: str = "gray") -> None:
        """Set the connection status message - now handled by main window status bar."""
        # Status updates are now handled by the main window's status bar
        # This method is kept for compatibility but does nothing
        pass
    
    def complete_wizard(self) -> None:
        """Complete the wizard and transition to chat."""
        # Don't call hide() - let the parent handle cleanup
        # Just call the completion callback
        if self.on_wizard_complete:
            self.on_wizard_complete()
    
    def get_username(self) -> str:
        """Get the current username."""
        return self.username
    
    
    # Placeholder text handling methods (copied from ModernChatWindow)
    
    def _setup_placeholder_text(self, textbox: ctk.CTkTextbox, placeholder: str) -> None:
        """Set up placeholder text for a CTkTextbox that disappears when user types."""
        textbox._placeholder_text = placeholder
        textbox._is_placeholder = True
        
        textbox.insert("0.0", placeholder)
        textbox.configure(text_color=("gray50", "gray50"))
        
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
            textbox.configure(text_color=("gray10", "gray90"))
            textbox._is_placeholder = False
    
    def _restore_placeholder(self, textbox: ctk.CTkTextbox) -> None:
        """Restore placeholder text if textbox is empty."""
        textbox.delete("0.0", "end")
        textbox.insert("0.0", textbox._placeholder_text)
        textbox.configure(text_color=("gray50", "gray50"))
        textbox._is_placeholder = True
    
    def _get_textbox_content(self, textbox: ctk.CTkTextbox) -> str:
        """Get the actual content of textbox, excluding placeholder text."""
        if not textbox or not textbox.winfo_exists():
            return ""
        if getattr(textbox, '_is_placeholder', False):
            return ""
        try:
            return textbox.get("0.0", "end-1c").strip()
        except Exception as e:
            logger.debug(f"Could not get textbox content: {e}")
            return ""
    

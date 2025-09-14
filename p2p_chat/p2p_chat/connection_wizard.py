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
        self.wizard_frame: Optional[ctk.CTk] = None  # Can be CTk or CTkFrame
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
        if self.wizard_frame:
            self.wizard_frame.grid_columnconfigure(0, weight=1)
        # Don't give weight to content area - let it expand naturally
        # self.wizard_frame.grid_rowconfigure(2, weight=1)  # Content area
        
    def _setup_ui(self) -> None:
        """Set up the wizard UI structure."""
        # Header with title and progress
        self._setup_header()
        
        # Content area - use wizard frame directly for content
        # Note: content_frame is used as a reference to wizard_frame for content placement
        if self.wizard_frame:
            self.wizard_frame.grid_columnconfigure(0, weight=1)
        
        # Navigation area
        self._setup_navigation()
    
    def _setup_header(self) -> None:
        """Set up the wizard header with progress indicators only."""
        # Progress indicators - positioned much closer to top
        self.progress_frame = ctk.CTkFrame(self.wizard_frame, fg_color="transparent")
        self.progress_frame.grid(row=0, column=0, pady=(2, 0), padx=20, sticky="ew")
        self.progress_frame.grid_columnconfigure(0, weight=1)  # Center the steps container
        
        # Create a dynamic-width container for the steps - compact height
        self.steps_container = ctk.CTkFrame(self.progress_frame, fg_color="transparent", height=55)
        self.steps_container.grid(row=0, column=0, sticky="n")  # Align to top
        self.steps_container.grid_propagate(False)
        # Initial configuration will be set by _update_progress_indicators()
        
        self._update_progress_indicators()
    
    def _setup_navigation(self) -> None:
        """Set up the navigation buttons."""
        self.navigation_frame = ctk.CTkFrame(self.wizard_frame, fg_color="transparent")
        self.navigation_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(5, 10))
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
        """Update the progress step indicators with stable positioning - no flickering."""
        # Define all possible steps in order (maximum 7 steps)
        all_steps = [
            ("1", WizardStep.WELCOME),
            ("2", WizardStep.USERNAME),
            ("3", WizardStep.CONNECTION_TYPE),
            ("4", WizardStep.CREATE_CHAT),
            ("5", WizardStep.JOIN_CHAT),
            ("6", WizardStep.SHARE_INVITE),
            ("7", WizardStep.SHARE_RETURN),
            ("8", WizardStep.WAIT_FOR_RETURN),
            ("9", WizardStep.WAITING_CONNECTION)
        ]
        
        # Determine which steps should be visible based on connection type
        if self.connection_type == "create":
            visible_step_enums = [
                WizardStep.WELCOME,
                WizardStep.USERNAME,
                WizardStep.CONNECTION_TYPE,
                WizardStep.CREATE_CHAT,
                WizardStep.SHARE_INVITE,
                WizardStep.WAIT_FOR_RETURN,
                WizardStep.WAITING_CONNECTION
            ]
        elif self.connection_type == "join":
            visible_step_enums = [
                WizardStep.WELCOME,
                WizardStep.USERNAME,
                WizardStep.CONNECTION_TYPE,
                WizardStep.JOIN_CHAT,
                WizardStep.SHARE_RETURN,
                WizardStep.WAITING_CONNECTION
            ]
        else:
            visible_step_enums = [
                WizardStep.WELCOME,
                WizardStep.USERNAME,
                WizardStep.CONNECTION_TYPE
            ]
        
        # Create indicators if they don't exist (only once)
        if not self.step_indicators:
            # Create all possible indicators (9 max) but hide them initially
            for i, (number, step_enum) in enumerate(all_steps):
                step_frame = ctk.CTkFrame(
                    self.steps_container,
                    width=38,
                    height=38,
                    corner_radius=19,
                    fg_color=("gray60", "gray40")
                )
                step_frame.grid(row=0, column=i, padx=8, pady=3, sticky="")
                step_frame.grid_propagate(False)
                step_frame.grid_remove()  # Hide by default
                
                # Make first 3 steps bigger initially
                initial_font_size = 22 if number in ["1", "2", "3"] else 18
                step_label = ctk.CTkLabel(
                    step_frame,
                    text=number,
                    font=ctk.CTkFont(size=initial_font_size, weight="bold"),
                    text_color=("gray30", "gray70"),
                    fg_color="transparent"
                )
                step_label.place(relx=0.5, rely=0.5, anchor="center")
                self.step_indicators.append(step_frame)
        
        # Calculate container width based on visible steps
        step_width = 60
        container_width = len(visible_step_enums) * step_width
        container_width = max(container_width, 200)
        self.steps_container.configure(width=container_width)
        
        # Clear all column configurations
        for i in range(9):  # Clear all 9 columns
            self.steps_container.grid_columnconfigure(i, weight=0)
        
        # Show/hide and configure visible indicators
        visible_count = 0
        for i, (number, step_enum) in enumerate(all_steps):
            if i < len(self.step_indicators):
                step_frame = self.step_indicators[i]
                
                if step_enum in visible_step_enums:
                    # Show this step
                    step_frame.grid()
                    self.steps_container.grid_columnconfigure(visible_count, weight=1)
                    
                    # Determine if this step is current or completed
                    is_current = self.current_step == step_enum
                    is_completed = self._is_step_completed(step_enum)
                    
                    # Set color based on status
                    if is_current:
                        fg_color = ("#4A90E2", "#4A90E2")  # Blue
                        text_color = ("white", "white")
                    elif is_completed:
                        fg_color = ("#5CB85C", "#5CB85C")  # Green
                        text_color = ("white", "white")
                    else:
                        fg_color = ("gray60", "gray40")  # Grey
                        text_color = ("gray30", "gray70")
                    
                    # Update frame properties
                    if is_current:
                        step_frame.configure(
                            width=48,
                            height=48,
                            corner_radius=24,
                            fg_color=fg_color
                        )
                        step_frame.grid_configure(padx=6, pady=3)
                    else:
                        step_frame.configure(
                            width=38,
                            height=38,
                            corner_radius=19,
                            fg_color=fg_color
                        )
                        step_frame.grid_configure(padx=8, pady=3)
                    
                    # Update label properties
                    # Make first 3 steps bigger (steps 1, 2, 3)
                    if number in ["1", "2", "3"]:
                        font_size = 26 if is_current else 22
                    else:
                        font_size = 22 if is_current else 18
                    step_label = step_frame.winfo_children()[0]
                    step_label.configure(
                        text=number,
                        font=ctk.CTkFont(size=font_size, weight="bold"),
                        text_color=text_color
                    )
                    
                    visible_count += 1
                else:
                    # Hide this step
                    step_frame.grid_remove()
    
    def _resize_window_to_content(self) -> None:
        """
        Resize the window to fit the content height.
        
        NOTE: This method is currently disabled to prevent constant window resizing
        during wizard navigation. The main window is now set to a fixed large size
        (1000x800) that accommodates all wizard steps without needing resizing.
        """
        if not self.current_content:
            return
        
        # Get the actual root window (not the frame)
        root_window = self.parent.winfo_toplevel()
        
        # Update the window to calculate the required size
        root_window.update_idletasks()
        
        # Get the current window size
        current_width = root_window.winfo_width()
        current_height = root_window.winfo_height()
        
        # Calculate the required height by measuring the entire wizard frame
        wizard_height = self.wizard_frame.winfo_reqheight() if self.wizard_frame else 0
        
        # Add extra padding for window decorations, borders, and safety margin
        # Increased padding to ensure title and all elements are visible
        window_padding = 250  # Extra padding for window title bar, borders, etc.
        
        required_height = wizard_height + window_padding
        
        # Set minimum height - increased to ensure title is always visible
        min_height = 600
        new_height = max(required_height, min_height)
        
        # Debug information
        print(f"Debug - Wizard height: {wizard_height}, Required: {required_height}, New: {new_height}, Current: {current_height}")
        
        # Only resize if the height has changed significantly and not in fullscreen
        if abs(new_height - current_height) > 50:  # Increased threshold to prevent constant resizing
            try:
                # Check if window is in fullscreen mode
                if not root_window.attributes('-fullscreen'):
                    root_window.geometry(f"{current_width}x{new_height}")
                else:
                    # In fullscreen, just ensure content is properly centered
                    self._center_content_in_fullscreen()
            except Exception as e:
                # If resizing fails, just log it and continue
                print(f"Window resize failed: {e}")
    
    def _center_content_in_fullscreen(self) -> None:
        """Center content when in fullscreen mode."""
        try:
            # Get the root window
            root_window = self.parent.winfo_toplevel()
            
            # Get screen dimensions
            screen_width = root_window.winfo_screenwidth()
            screen_height = root_window.winfo_screenheight()
            
            # Calculate wizard content dimensions
            if self.wizard_frame:
                wizard_width = self.wizard_frame.winfo_reqwidth()
                wizard_height = self.wizard_frame.winfo_reqheight()
                
                # Center the wizard frame
                x_offset = (screen_width - wizard_width) // 2
                y_offset = (screen_height - wizard_height) // 2
                
                # Apply centering by adjusting grid configuration
                # Only apply grid_configure if it's a frame, not the main window
                try:
                    # Use getattr to avoid type checker issues
                    grid_configure = getattr(self.wizard_frame, 'grid_configure', None)
                    if grid_configure:
                        grid_configure(padx=x_offset//2, pady=y_offset//2)
                except Exception:
                    # CTk doesn't have grid_configure, skip centering
                    pass
            
        except Exception as e:
            print(f"Error centering content in fullscreen: {e}")
    
    def _is_step_completed(self, step: WizardStep) -> bool:
        """Check if a step has been completed."""
        # Define the step order for each flow
        if self.connection_type == "create":
            step_order = [
                WizardStep.WELCOME,
                WizardStep.USERNAME, 
                WizardStep.CONNECTION_TYPE,
                WizardStep.CREATE_CHAT,
                WizardStep.SHARE_INVITE,
                WizardStep.WAIT_FOR_RETURN,
                WizardStep.WAITING_CONNECTION
            ]
        elif self.connection_type == "join":
            step_order = [
                WizardStep.WELCOME,
                WizardStep.USERNAME,
                WizardStep.CONNECTION_TYPE, 
                WizardStep.JOIN_CHAT,
                WizardStep.SHARE_RETURN,
                WizardStep.WAITING_CONNECTION
            ]
        else:
            step_order = [
                WizardStep.WELCOME,
                WizardStep.USERNAME,
                WizardStep.CONNECTION_TYPE
            ]
        
        # Find the current step index
        try:
            current_index = step_order.index(self.current_step)
        except ValueError:
            current_index = 0
        
        # Find the step index we're checking
        try:
            step_index = step_order.index(step)
        except ValueError:
            return False
        
        # A step is completed if it comes before the current step
        return step_index < current_index
    
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
        
        # Disabled automatic resizing to prevent constant window resizing
        # The window is now set to a fixed large size that accommodates all wizard steps
        # self.parent.after(100, self._resize_window_to_content)
    
    def _show_welcome_step(self) -> None:
        """Show the welcome step with simplified design."""
        self.current_content = ctk.CTkFrame(self.wizard_frame, corner_radius=0)
        self.current_content.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 0))
        self.current_content.grid_columnconfigure(0, weight=1)
        
        # Welcome content
        welcome_label = ctk.CTkLabel(
            self.current_content,
            text="👋 Welcome to SuperSecureChat!",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("gray10", "gray90")
        )
        welcome_label.grid(row=0, column=0, pady=(10, 10))
        
        # Features list
        features_text = ctk.CTkLabel(
            self.current_content,
            text="🔒 End-to-end encrypted messaging\n"
                 "🌐 Direct peer-to-peer connection\n"
                 "📁 Secure file transfers\n"
                 "🎤 Real-time voice chat\n"
                 "🚫 No servers - complete privacy\n"
                 "⚠️ Chats not saved - automatically lost on disconnect",
            font=ctk.CTkFont(size=14),
            text_color=("gray40", "gray60"),
            justify="center"
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
        """Show the username entry step with simplified design."""
        self.current_content = ctk.CTkFrame(self.wizard_frame, corner_radius=0)
        self.current_content.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 0))
        self.current_content.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.current_content,
            text="👤 Choose Your Display Name",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, pady=(0, 15))
        
        # Instructions
        instructions_label = ctk.CTkLabel(
            self.current_content,
            text="Enter a name that will be displayed to other participants.\n"
                 "This can be changed later in the chat settings.",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            justify="center"
        )
        instructions_label.grid(row=1, column=0, pady=(0, 20))
        
        # Username entry
        self.username_entry = ctk.CTkEntry(
            self.current_content,
            placeholder_text="Enter your display name (optional)",
            font=ctk.CTkFont(size=14),
            height=40,
            corner_radius=8,
            width=400
        )
        self.username_entry.grid(row=2, column=0, pady=(0, 15))
        
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
        note_label.grid(row=3, column=0, pady=(0, 30))
    
    
    def _show_connection_type_step(self) -> None:
        """Show the connection type selection step with simplified design."""
        self.current_content = ctk.CTkFrame(self.wizard_frame, corner_radius=0)
        self.current_content.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 0))
        self.current_content.grid_columnconfigure(0, weight=1)
        self.current_content.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.current_content,
            text="🔗 Choose Connection Type",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Create chat option
        create_frame = ctk.CTkFrame(self.current_content, corner_radius=0)
        create_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=0)
        create_frame.grid_columnconfigure(0, weight=1)
        
        create_icon = ctk.CTkLabel(
            create_frame,
            text="🚀",
            font=ctk.CTkFont(size=36)
        )
        create_icon.grid(row=0, column=0, pady=(20, 10))
        
        create_title = ctk.CTkLabel(
            create_frame,
            text="Create New Chat",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray10", "gray90")
        )
        create_title.grid(row=1, column=0, pady=(0, 10))
        
        create_desc = ctk.CTkLabel(
            create_frame,
            text="Start a new secure chat room\nand invite others to join",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            justify="center"
        )
        create_desc.grid(row=2, column=0, pady=(0, 15))
        
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
        self.create_btn.grid(row=3, column=0, pady=(0, 20))
        
        # Join chat option
        join_frame = ctk.CTkFrame(self.current_content, corner_radius=0)
        join_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=0)
        join_frame.grid_columnconfigure(0, weight=1)
        
        join_icon = ctk.CTkLabel(
            join_frame,
            text="🔗",
            font=ctk.CTkFont(size=36)
        )
        join_icon.grid(row=0, column=0, pady=(20, 10))
        
        join_title = ctk.CTkLabel(
            join_frame,
            text="Join Existing Chat",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray10", "gray90")
        )
        join_title.grid(row=1, column=0, pady=(0, 10))
        
        join_desc = ctk.CTkLabel(
            join_frame,
            text="Connect to an existing\nchat room using an invite key",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            justify="center"
        )
        join_desc.grid(row=2, column=0, pady=(0, 15))
        
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
        self.join_btn.grid(row=3, column=0, pady=(0, 20))
    
    def _show_create_chat_step(self) -> None:
        """Show the create chat step - just shows that chat is being created."""
        self.current_content = ctk.CTkFrame(self.wizard_frame, corner_radius=0)
        self.current_content.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 0))
        self.current_content.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.current_content,
            text="🚀 Creating Your Chat Room",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, pady=(0, 15))
        
        # Instructions
        instructions_label = ctk.CTkLabel(
            self.current_content,
            text="Your secure chat room is being created...\n"
                 "You'll be able to share your invite key in the next step.",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            justify="center"
        )
        instructions_label.grid(row=1, column=0, pady=(0, 20))
        
        # Progress indicator
        self.progress_bar = ctk.CTkProgressBar(
            self.current_content,
            width=300,
            height=20,
            corner_radius=8
        )
        self.progress_bar.grid(row=2, column=0, pady=(0, 20))
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
        self.continue_btn.grid(row=3, column=0, pady=(0, 30))
    
    def _show_join_chat_step(self) -> None:
        """Show the join chat step."""
        self.current_content = ctk.CTkFrame(self.wizard_frame, corner_radius=0)
        self.current_content.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 0))
        self.current_content.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.current_content,
            text="🔗 Joining a Chat Room",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, pady=(0, 15))
        
        # Instructions
        instructions_label = ctk.CTkLabel(
            self.current_content,
            text="Paste the invite key you received from the chat creator below.\n"
                 "You'll then receive a return key to share back with them.",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            justify="center"
        )
        instructions_label.grid(row=1, column=0, pady=(0, 20))
        
        # Invite key input section
        invite_label = ctk.CTkLabel(
            self.current_content,
            text="📨 Invite Key",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray30", "gray70")
        )
        invite_label.grid(row=2, column=0, pady=(15, 10))
        
        self.join_entry = ctk.CTkTextbox(
            self.current_content,
            height=100,
            font=ctk.CTkFont(size=12, family="monospace"),
            corner_radius=8
        )
        self.join_entry.grid(row=3, column=0, sticky="ew", padx=0, pady=(0, 15))
        
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
        self.join_submit_btn.grid(row=4, column=0, pady=(0, 20))
    
    def _show_share_invite_step(self) -> None:
        """Show the share invite key step."""
        self.current_content = ctk.CTkFrame(self.wizard_frame, corner_radius=0)
        self.current_content.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 0))
        self.current_content.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.current_content,
            text="📤 Share Your Invite Key",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, pady=(0, 15))
        
        # Instructions
        instructions_label = ctk.CTkLabel(
            self.current_content,
            text="Copy and share this invite key with the person you want to chat with.\n"
                 "They will need to enter it in their app to join your chat.",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            justify="center"
        )
        instructions_label.grid(row=1, column=0, pady=(0, 20))
        
        # Invite key display section with copy button
        invite_section = ctk.CTkFrame(self.current_content, fg_color="transparent")
        invite_section.grid(row=2, column=0, sticky="ew", pady=(15, 10))
        invite_section.grid_columnconfigure(0, weight=1)
        invite_section.grid_columnconfigure(1, weight=0)
        
        invite_label = ctk.CTkLabel(
            invite_section,
            text="📤 Your Invite Key",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray30", "gray70")
        )
        invite_label.grid(row=0, column=0, sticky="w")
        
        self.copy_invite_btn = ctk.CTkButton(
            invite_section,
            text="📋",
            width=30,
            height=30,
            font=ctk.CTkFont(size=14),
            corner_radius=6,
            command=self._copy_invite_key,
            fg_color=("gray45", "gray35"),
            hover_color=("gray55", "gray25")
        )
        self.copy_invite_btn.grid(row=0, column=1, sticky="e", padx=(10, 0))
        
        self.invite_text = ctk.CTkTextbox(
            self.current_content,
            height=100,
            font=ctk.CTkFont(size=12, family="monospace"),
            corner_radius=8,
            state="disabled"
        )
        self.invite_text.grid(row=3, column=0, sticky="ew", padx=0, pady=(0, 20))
        
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
        self.next_step_btn.grid(row=5, column=0, pady=(0, 30))
        
        # Add tooltip for the wait for return key button
        self._add_tooltip(self.next_step_btn, 
                         "IMPORTANT: First share your invite key above with your peer!\n\n"
                         "Then click this button to wait for their return key.\n"
                         "Once you receive their return key, paste it to complete the connection.")
    
    def _show_wait_for_return_step(self) -> None:
        """Show the wait for return key step."""
        self.current_content = ctk.CTkFrame(self.wizard_frame, corner_radius=0)
        self.current_content.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 0))
        self.current_content.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.current_content,
            text="⏳ Waiting for Return Key",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, pady=(0, 15))
        
        # Instructions
        instructions_label = ctk.CTkLabel(
            self.current_content,
            text="Wait for your peer to send you their return key.\n"
                 "Once you receive it, paste it below to establish the connection.",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            justify="center"
        )
        instructions_label.grid(row=1, column=0, pady=(0, 20))
        
        # Return key input
        return_label = ctk.CTkLabel(
            self.current_content,
            text="📥 Return Key (Paste Here)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray30", "gray70")
        )
        return_label.grid(row=2, column=0, pady=(15, 10))
        
        self.return_entry = ctk.CTkTextbox(
            self.current_content,
            height=100,
            font=ctk.CTkFont(size=12, family="monospace"),
            corner_radius=8
        )
        self.return_entry.grid(row=3, column=0, sticky="ew", padx=0, pady=(0, 15))
        
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
        self.connect_btn.grid(row=4, column=0, pady=(0, 30))
    
    def _show_share_return_step(self) -> None:
        """Show the share return key step."""
        self.current_content = ctk.CTkFrame(self.wizard_frame, corner_radius=0)
        self.current_content.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 0))
        self.current_content.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.current_content,
            text="📤 Share Your Return Key",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, pady=(0, 15))
        
        # Instructions
        instructions_label = ctk.CTkLabel(
            self.current_content,
            text="Copy and share this return key with the chat creator.\n"
                 "They will use it to complete the connection.",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            justify="center"
        )
        instructions_label.grid(row=1, column=0, pady=(0, 20))
        
        # Return key display section with copy button
        return_section = ctk.CTkFrame(self.current_content, fg_color="transparent")
        return_section.grid(row=2, column=0, sticky="ew", pady=(15, 10))
        return_section.grid_columnconfigure(0, weight=1)
        return_section.grid_columnconfigure(1, weight=0)
        
        return_label = ctk.CTkLabel(
            return_section,
            text="📤 Your Return Key",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray30", "gray70")
        )
        return_label.grid(row=0, column=0, sticky="w")
        
        self.copy_return_btn = ctk.CTkButton(
            return_section,
            text="📋",
            width=30,
            height=30,
            font=ctk.CTkFont(size=14),
            corner_radius=6,
            command=self._copy_return_key,
            fg_color=("gray45", "gray35"),
            hover_color=("gray55", "gray25")
        )
        self.copy_return_btn.grid(row=0, column=1, sticky="e", padx=(10, 0))
        
        self.return_display_text = ctk.CTkTextbox(
            self.current_content,
            height=100,
            font=ctk.CTkFont(size=12, family="monospace"),
            corner_radius=8,
            state="disabled"
        )
        self.return_display_text.grid(row=3, column=0, sticky="ew", padx=0, pady=(0, 20))
        
        # Waiting message
        waiting_label = ctk.CTkLabel(
            self.current_content,
            text="⏳ Waiting for connection...",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray50")
        )
        waiting_label.grid(row=5, column=0, pady=(0, 30))
    
    def _show_waiting_connection_step(self) -> None:
        """Show the waiting for connection step."""
        self.current_content = ctk.CTkFrame(self.wizard_frame, corner_radius=0)
        self.current_content.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 0))
        self.current_content.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.current_content,
            text="⏳ Establishing Connection",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, pady=(0, 15))
        
        # Status message (removed - using main status bar instead)
        status_text = ctk.CTkLabel(
            self.current_content,
            text="Waiting for peer connection...",
            font=ctk.CTkFont(size=14),
            text_color=("gray40", "gray60")
        )
        status_text.grid(row=1, column=0, pady=(0, 20))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.current_content,
            width=300,
            height=20,
            corner_radius=8
        )
        self.progress_bar.grid(row=2, column=0, pady=(0, 20))
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
        instructions_label.grid(row=3, column=0, pady=(0, 30))
    
    def _update_navigation(self) -> None:
        """Update navigation buttons based on current step."""
        # Show/hide back button
        if len(self.step_history) > 1:
            self.back_btn.grid()
        else:
            self.back_btn.grid_remove()
        
        # Update next button text and visibility
        if self.current_step == WizardStep.WELCOME:
            self.next_btn.configure(text="Get Started")
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
            # Show temporary feedback by changing button text briefly
            original_text = self.copy_invite_btn.cget("text")
            self.copy_invite_btn.configure(text="✅")
            self.parent.after(1500, lambda: self.copy_invite_btn.configure(text=original_text))
    
    def _copy_return_key(self) -> None:
        """Copy return key to clipboard."""
        if self.return_key:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(self.return_key)
            # Show temporary feedback by changing button text briefly
            if hasattr(self, 'copy_return_btn'):
                original_text = self.copy_return_btn.cget("text")
                self.copy_return_btn.configure(text="✅")
                self.parent.after(1500, lambda: self.copy_return_btn.configure(text=original_text))
    
    
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
        # Store placeholder state in a dictionary instead of attributes
        if not hasattr(self, '_placeholder_states'):
            self._placeholder_states = {}
        
        self._placeholder_states[id(textbox)] = {
            'placeholder_text': placeholder,
            'is_placeholder': True
        }
        
        textbox.insert("0.0", placeholder)
        textbox.configure(text_color=("gray50", "gray50"))
        
        textbox.bind("<Button-1>", lambda e: self._on_textbox_click(textbox))
        textbox.bind("<KeyPress>", lambda e: self._on_textbox_keypress(textbox, e))
        textbox.bind("<Control-v>", lambda e: self._on_textbox_paste(textbox, e))
        textbox.bind("<Shift-Insert>", lambda e: self._on_textbox_paste(textbox, e))
        textbox.bind("<FocusOut>", lambda e: self._on_textbox_focus_out(textbox))
    
    def _on_textbox_click(self, textbox: ctk.CTkTextbox) -> None:
        """Handle click on textbox with placeholder text."""
        if self._is_placeholder(textbox):
            self._clear_placeholder(textbox)
    
    def _on_textbox_keypress(self, textbox: ctk.CTkTextbox, event) -> None:
        """Handle key press on textbox with placeholder text."""
        if self._is_placeholder(textbox):
            self._clear_placeholder(textbox)
    
    def _on_textbox_paste(self, textbox: ctk.CTkTextbox, event) -> None:
        """Handle paste on textbox with placeholder text."""
        if self._is_placeholder(textbox):
            self._clear_placeholder(textbox)
    
    def _on_textbox_focus_out(self, textbox: ctk.CTkTextbox) -> None:
        """Handle focus out - restore placeholder if empty."""
        content = textbox.get("0.0", "end-1c").strip()
        if not content:
            self._restore_placeholder(textbox)
    
    def _is_placeholder(self, textbox: ctk.CTkTextbox) -> bool:
        """Check if textbox is showing placeholder text."""
        if not hasattr(self, '_placeholder_states'):
            return False
        state = self._placeholder_states.get(id(textbox))
        return bool(state and state.get('is_placeholder', False))
    
    def _get_placeholder_text(self, textbox: ctk.CTkTextbox) -> str:
        """Get placeholder text for textbox."""
        if not hasattr(self, '_placeholder_states'):
            return ""
        state = self._placeholder_states.get(id(textbox))
        return state.get('placeholder_text', "") if state else ""
    
    def _clear_placeholder(self, textbox: ctk.CTkTextbox) -> None:
        """Clear placeholder text and set normal text color."""
        if self._is_placeholder(textbox):
            textbox.delete("0.0", "end")
            textbox.configure(text_color=("gray10", "gray90"))
            if hasattr(self, '_placeholder_states') and id(textbox) in self._placeholder_states:
                self._placeholder_states[id(textbox)]['is_placeholder'] = False
    
    def _restore_placeholder(self, textbox: ctk.CTkTextbox) -> None:
        """Restore placeholder text if textbox is empty."""
        textbox.delete("0.0", "end")
        placeholder_text = self._get_placeholder_text(textbox)
        textbox.insert("0.0", placeholder_text)
        textbox.configure(text_color=("gray50", "gray50"))
        if hasattr(self, '_placeholder_states') and id(textbox) in self._placeholder_states:
            self._placeholder_states[id(textbox)]['is_placeholder'] = True
    
    def _get_textbox_content(self, textbox: ctk.CTkTextbox) -> str:
        """Get the actual content of textbox, excluding placeholder text."""
        if not textbox or not textbox.winfo_exists():
            return ""
        if self._is_placeholder(textbox):
            return ""
        try:
            return textbox.get("0.0", "end-1c").strip()
        except Exception as e:
            logger.debug(f"Could not get textbox content: {e}")
            return ""
    
    def _add_tooltip(self, widget, text: str) -> None:
        """Add a tooltip to a widget that shows on hover with delay."""
        def show_tooltip(event):
            # Don't show tooltip if one already exists
            if hasattr(widget, '_tooltip') and widget._tooltip:
                return
            
            # Cancel any existing delay safely
            if hasattr(widget, '_tooltip_delay') and widget._tooltip_delay:
                try:
                    widget.after_cancel(widget._tooltip_delay)
                except ValueError:
                    # Delay might have already been executed or cancelled
                    pass
                widget._tooltip_delay = None
            
            # Set a delay before showing tooltip (1.5 seconds)
            widget._tooltip_delay = widget.after(1500, lambda: _create_tooltip(event))
        
        def _create_tooltip(event):
            # Don't show tooltip if one already exists
            if hasattr(widget, '_tooltip') and widget._tooltip:
                return
                
            # Create tooltip window
            tooltip = ctk.CTkToplevel()
            tooltip.wm_overrideredirect(True)  # Remove window decorations
            tooltip.wm_attributes("-topmost", True)  # Keep on top
            
            # Create tooltip label with better readability
            tooltip_label = ctk.CTkLabel(
                tooltip,
                text=text,
                font=ctk.CTkFont(size=13, weight="normal"),  # Larger, clearer font
                text_color=("black", "white"),  # High contrast colors
                fg_color=("white", "black"),  # High contrast background
                corner_radius=8,
                padx=12,  # More padding
                pady=8,   # More padding
                wraplength=350  # Allow text wrapping for long messages
            )
            tooltip_label.pack()
            
            # Position tooltip near mouse cursor but ensure it stays on screen
            x = event.x_root + 15
            y = event.y_root + 15
            
            # Get screen dimensions to keep tooltip on screen
            screen_width = tooltip.winfo_screenwidth()
            screen_height = tooltip.winfo_screenheight()
            
            # Adjust position if tooltip would go off screen
            tooltip.update_idletasks()
            tooltip_width = tooltip.winfo_reqwidth()
            tooltip_height = tooltip.winfo_reqheight()
            
            if x + tooltip_width > screen_width:
                x = event.x_root - tooltip_width - 15
            if y + tooltip_height > screen_height:
                y = event.y_root - tooltip_height - 15
                
            tooltip.geometry(f"+{x}+{y}")
            
            # Store tooltip reference for cleanup
            widget._tooltip = tooltip
            
            # Hide tooltip after 10 seconds (even longer for important info)
            tooltip.after(10000, lambda: hide_tooltip())
        
        def hide_tooltip():
            # Cancel any pending tooltip delay safely
            if hasattr(widget, '_tooltip_delay') and widget._tooltip_delay:
                try:
                    widget.after_cancel(widget._tooltip_delay)
                except ValueError:
                    # Delay might have already been executed or cancelled
                    pass
                widget._tooltip_delay = None
            
            if hasattr(widget, '_tooltip') and widget._tooltip:
                try:
                    widget._tooltip.destroy()
                    widget._tooltip = None
                except:
                    pass
        
        # Bind events
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", lambda e: hide_tooltip())
        widget.bind("<Button-1>", lambda e: hide_tooltip())
    

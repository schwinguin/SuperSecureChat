"""
Custom File Dialog for the P2P chat application.
Provides modern, large file dialogs that appear on top of other windows.
"""

import customtkinter as ctk
import os
import logging
from typing import Optional, List, Tuple, Callable
from tkinter import messagebox

logger = logging.getLogger(__name__)


class CustomFileDialog(ctk.CTkToplevel):
    """Custom file dialog with modern UI that appears on top."""
    
    def __init__(self, parent, dialog_type: str = "open", title: str = "Select File", 
                 initialdir: str = None, initialfile: str = None, 
                 filetypes: List[Tuple[str, str]] = None, on_result: Callable = None):
        super().__init__(parent)
        
        self.dialog_type = dialog_type  # "open" or "save"
        self.title_text = title
        self.initialdir = initialdir or os.path.expanduser("~")
        self.initialfile = initialfile or ""
        self.filetypes = filetypes or [("All Files", "*.*")]
        self.on_result = on_result
        self.result = None
        
        # Dialog configuration
        self.title(title)
        self.geometry("800x600")
        self.resizable(True, True)
        
        # Make dialog always on top (non-modal for better compatibility)
        self.transient(parent)
        self.lift()
        self.attributes("-topmost", True)
        
        # Current directory and file list
        self.current_dir = self.initialdir
        self.current_files = []
        self.selected_file = None
        
        self._setup_ui()
        self._load_directory()
        
        # Center on parent and ensure visibility
        self.after(100, self._center_on_parent)
        self.after(200, self._ensure_visible)
    
    
    def _ensure_visible(self):
        """Ensure dialog is visible and on top."""
        try:
            self.lift()
            self.focus_force()
            self.attributes("-topmost", True)
        except Exception as e:
            logger.warning(f"Could not ensure dialog visibility: {e}")
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        try:
            # Scroll the scrollable frame
            if event.delta:
                # Windows and MacOS
                delta = int(event.delta / 120)
            else:
                # Linux
                if event.num == 4:
                    delta = -1
                elif event.num == 5:
                    delta = 1
                else:
                    delta = 0
            
            # Scroll the frame
            self.file_listbox._parent_canvas.yview_scroll(delta, "units")
        except Exception as e:
            logger.warning(f"Mouse wheel scroll error: {e}")
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        # Main frame
        main_frame = ctk.CTkFrame(self, corner_radius=0)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text=self.title_text,
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(20, 15))
        
        # Current directory display
        dir_frame = ctk.CTkFrame(main_frame)
        dir_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(dir_frame, text="Current Directory:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.dir_label = ctk.CTkLabel(
            dir_frame,
            text=self.current_dir,
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40")
        )
        self.dir_label.pack(anchor="w", padx=10, pady=(0, 10))
        
        # File list frame
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # File list header
        header_frame = ctk.CTkFrame(list_frame)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(header_frame, text="Files and Folders", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=5)
        
        # File list with scrollbar
        self.file_listbox = ctk.CTkScrollableFrame(list_frame, height=300)
        self.file_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Bind mouse wheel events for scrolling
        self.file_listbox.bind("<MouseWheel>", self._on_mousewheel)
        self.file_listbox.bind("<Button-4>", self._on_mousewheel)  # Linux scroll up
        self.file_listbox.bind("<Button-5>", self._on_mousewheel)  # Linux scroll down
        
        # Bind keyboard navigation
        self.file_listbox.bind("<KeyPress>", self._on_key_press)
        self.file_listbox.focus_set()  # Make it focusable
        
        # Store file items for easy access
        self.file_items = []
        self.selected_index = -1
        
        # File name input (for save dialog)
        if self.dialog_type == "save":
            input_frame = ctk.CTkFrame(main_frame)
            input_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            ctk.CTkLabel(input_frame, text="File Name:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
            
            self.filename_entry = ctk.CTkEntry(
                input_frame,
                placeholder_text="Enter filename...",
                font=ctk.CTkFont(size=14),
                height=35
            )
            self.filename_entry.pack(fill="x", padx=10, pady=(0, 10))
            self.filename_entry.insert(0, self.initialfile)
            
            # Bind events to enable/disable save button based on filename input
            self.filename_entry.bind("<KeyRelease>", self._on_filename_change)
            self.filename_entry.bind("<Button-1>", self._on_filename_change)
        
        # File type filter
        filter_frame = ctk.CTkFrame(main_frame)
        filter_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(filter_frame, text="File Type:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.filetype_var = ctk.StringVar(value=self.filetypes[0][0])
        self.filetype_menu = ctk.CTkOptionMenu(
            filter_frame,
            values=[ft[0] for ft in self.filetypes],
            variable=self.filetype_var,
            command=self._on_filetype_change
        )
        self.filetype_menu.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=100,
            height=35,
            fg_color="gray",
            hover_color="darkgray"
        )
        cancel_btn.pack(side="right", padx=(10, 0), pady=10)
        
        # Open/Save button
        action_text = "Open" if self.dialog_type == "open" else "Save"
        self.action_btn = ctk.CTkButton(
            button_frame,
            text=action_text,
            command=self._on_action,
            width=100,
            height=35
        )
        self.action_btn.pack(side="right", padx=(10, 0), pady=10)
        
        # Initially disable action button (unless there's already a filename for save dialog)
        if self.dialog_type == "save" and self.initialfile:
            self.action_btn.configure(state="normal")
        else:
            self.action_btn.configure(state="disabled")
    
    def _center_on_parent(self):
        """Center dialog on parent window."""
        try:
            self.update_idletasks()
            
            # Get parent window position and size
            parent_x = self.master.winfo_x()
            parent_y = self.master.winfo_y()
            parent_width = self.master.winfo_width()
            parent_height = self.master.winfo_height()
            
            # Calculate center position
            x = parent_x + (parent_width - 800) // 2
            y = parent_y + (parent_height - 600) // 2
            
            # Ensure dialog is on screen
            x = max(0, x)
            y = max(0, y)
            
            self.geometry(f"800x600+{x}+{y}")
            logger.info(f"Custom file dialog centered at ({x}, {y})")
        except Exception as e:
            logger.warning(f"Could not center dialog: {e}")
            self.geometry("+100+100")
    
    def _load_directory(self):
        """Load files and folders from current directory."""
        try:
            # Clear existing items
            for widget in self.file_listbox.winfo_children():
                widget.destroy()
            
            self.current_files = []
            self.file_items.clear()
            self.selected_index = -1
            
            # Add parent directory option (if not at root)
            if self.current_dir != os.path.dirname(self.current_dir):
                self._add_file_item("..", "📁", is_directory=True)
            
            # Get directory contents
            try:
                items = os.listdir(self.current_dir)
                items.sort(key=lambda x: (not os.path.isdir(os.path.join(self.current_dir, x)), x.lower()))
                
                for item in items:
                    item_path = os.path.join(self.current_dir, item)
                    if os.path.isdir(item_path):
                        self._add_file_item(item, "📁", is_directory=True)
                    else:
                        # Check file type filter
                        if self._matches_filetype(item):
                            self._add_file_item(item, "📄", is_directory=False)
            
            except PermissionError:
                self._add_file_item("Access Denied", "❌", is_directory=False, disabled=True)
            
            # Update directory label
            self.dir_label.configure(text=self.current_dir)
            
        except Exception as e:
            logger.error(f"Error loading directory: {e}")
            messagebox.showerror("Error", f"Could not load directory: {e}")
    
    def _add_file_item(self, name: str, icon: str, is_directory: bool, disabled: bool = False):
        """Add a file or folder item to the list."""
        item_frame = ctk.CTkFrame(self.file_listbox)
        item_frame.pack(fill="x", padx=5, pady=2)
        
        # Add to items list for navigation
        self.file_items.append(item_frame)
        
        # Icon and name
        icon_label = ctk.CTkLabel(item_frame, text=icon, font=ctk.CTkFont(size=16))
        icon_label.pack(side="left", padx=10, pady=8)
        
        name_label = ctk.CTkLabel(
            item_frame,
            text=name,
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        name_label.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=8)
        
        # Size info for files
        if not is_directory and not disabled:
            try:
                file_path = os.path.join(self.current_dir, name)
                size = os.path.getsize(file_path)
                size_text = self._format_file_size(size)
                size_label = ctk.CTkLabel(
                    item_frame,
                    text=size_text,
                    font=ctk.CTkFont(size=12),
                    text_color=("gray60", "gray40")
                )
                size_label.pack(side="right", padx=10, pady=8)
            except:
                pass
        
        # Bind click events
        if not disabled:
            # Store item data
            item_frame.item_name = name
            item_frame.item_type = is_directory
            item_frame.is_disabled = disabled
            
            # Single click for selection
            item_frame.bind("<Button-1>", lambda e, n=name, d=is_directory: self._on_item_click(n, d))
            icon_label.bind("<Button-1>", lambda e, n=name, d=is_directory: self._on_item_click(n, d))
            name_label.bind("<Button-1>", lambda e, n=name, d=is_directory: self._on_item_click(n, d))
            
            # Double-click to open/select
            item_frame.bind("<Double-Button-1>", lambda e, n=name, d=is_directory: self._on_item_double_click(n, d))
            icon_label.bind("<Double-Button-1>", lambda e, n=name, d=is_directory: self._on_item_double_click(n, d))
            name_label.bind("<Double-Button-1>", lambda e, n=name, d=is_directory: self._on_item_double_click(n, d))
            
            # Add hover effects
            item_frame.bind("<Enter>", lambda e, f=item_frame: self._on_item_hover(f, True))
            item_frame.bind("<Leave>", lambda e, f=item_frame: self._on_item_hover(f, False))
            icon_label.bind("<Enter>", lambda e, f=item_frame: self._on_item_hover(f, True))
            icon_label.bind("<Leave>", lambda e, f=item_frame: self._on_item_hover(f, False))
            name_label.bind("<Enter>", lambda e, f=item_frame: self._on_item_hover(f, True))
            name_label.bind("<Leave>", lambda e, f=item_frame: self._on_item_hover(f, False))
    
    def _format_file_size(self, size: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def _matches_filetype(self, filename: str) -> bool:
        """Check if filename matches current file type filter."""
        if not self.filetypes:
            return True
        
        current_type = self.filetype_var.get()
        for filetype_name, pattern in self.filetypes:
            if filetype_name == current_type:
                if pattern == "*.*":
                    return True
                # Simple pattern matching
                if filename.lower().endswith(pattern.replace("*", "").lower()):
                    return True
        return False
    
    def _on_item_hover(self, item_frame, is_entering):
        """Handle item hover effects."""
        try:
            if is_entering and not getattr(item_frame, 'is_disabled', False):
                item_frame.configure(fg_color=("gray85", "gray25"))
            else:
                item_frame.configure(fg_color=("gray90", "gray20"))
        except Exception as e:
            logger.warning(f"Hover effect error: {e}")
    
    def _on_item_click(self, name: str, is_directory: bool):
        """Handle file/folder item click."""
        if is_directory:
            # Navigate to directory
            if name == "..":
                self.current_dir = os.path.dirname(self.current_dir)
            else:
                self.current_dir = os.path.join(self.current_dir, name)
            self._load_directory()
        else:
            # Select file
            self.selected_file = name
            if self.dialog_type == "save":
                self.filename_entry.delete(0, "end")
                self.filename_entry.insert(0, name)
            self.action_btn.configure(state="normal")
    
    def _on_filename_change(self, event=None):
        """Handle filename entry changes to enable/disable save button."""
        if self.dialog_type == "save":
            filename = self.filename_entry.get().strip()
            if filename:
                self.action_btn.configure(state="normal")
            else:
                self.action_btn.configure(state="disabled")
    
    def _on_item_double_click(self, name: str, is_directory: bool):
        """Handle file/folder item double-click."""
        if is_directory:
            # Navigate to directory
            if name == "..":
                self.current_dir = os.path.dirname(self.current_dir)
            else:
                self.current_dir = os.path.join(self.current_dir, name)
            self._load_directory()
        else:
            # Select and confirm file
            self.selected_file = name
            if self.dialog_type == "save":
                self.filename_entry.delete(0, "end")
                self.filename_entry.insert(0, name)
            self._on_action()
    
    def _on_key_press(self, event):
        """Handle keyboard navigation."""
        try:
            if event.keysym == "Up":
                self._navigate_items(-1)
            elif event.keysym == "Down":
                self._navigate_items(1)
            elif event.keysym == "Return":
                if 0 <= self.selected_index < len(self.file_items):
                    item = self.file_items[self.selected_index]
                    if hasattr(item, 'item_name') and hasattr(item, 'item_type'):
                        if item.item_type:  # is_directory
                            self._on_item_click(item.item_name, item.item_type)
                        else:  # is file
                            self._on_item_double_click(item.item_name, item.item_type)
            elif event.keysym == "Escape":
                self._on_cancel()
        except Exception as e:
            logger.warning(f"Keyboard navigation error: {e}")
    
    def _navigate_items(self, direction):
        """Navigate through file items with keyboard."""
        if not self.file_items:
            return
        
        # Clear previous selection
        if 0 <= self.selected_index < len(self.file_items):
            self._clear_selection()
        
        # Move selection
        self.selected_index += direction
        self.selected_index = max(0, min(self.selected_index, len(self.file_items) - 1))
        
        # Highlight current selection
        if 0 <= self.selected_index < len(self.file_items):
            self._highlight_selection()
    
    def _clear_selection(self):
        """Clear current selection highlight."""
        if 0 <= self.selected_index < len(self.file_items):
            item = self.file_items[self.selected_index]
            item.configure(fg_color=("gray90", "gray20"))
    
    def _highlight_selection(self):
        """Highlight current selection."""
        if 0 <= self.selected_index < len(self.file_items):
            item = self.file_items[self.selected_index]
            item.configure(fg_color=("gray80", "gray30"))
    
    def _on_filetype_change(self, value):
        """Handle file type filter change."""
        self._load_directory()
    
    def _on_action(self):
        """Handle open/save button click."""
        if self.dialog_type == "open":
            if self.selected_file:
                self.result = os.path.join(self.current_dir, self.selected_file)
                self._cleanup_and_destroy()
        else:  # save
            filename = self.filename_entry.get().strip()
            if filename:
                self.result = os.path.join(self.current_dir, filename)
                self._cleanup_and_destroy()
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.result = None
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
        logger.debug("Custom file dialog destroyed")


def askopenfilename(parent=None, title="Select File", initialdir=None, 
                   filetypes=None, **kwargs) -> Optional[str]:
    """Custom file open dialog."""
    dialog = CustomFileDialog(
        parent=parent or ctk.CTk(),
        dialog_type="open",
        title=title,
        initialdir=initialdir,
        filetypes=filetypes
    )
    
    dialog.wait_window()
    return dialog.result


def asksaveasfilename(parent=None, title="Save File As", initialdir=None, 
                     initialfile=None, filetypes=None, **kwargs) -> Optional[str]:
    """Custom file save dialog."""
    dialog = CustomFileDialog(
        parent=parent or ctk.CTk(),
        dialog_type="save",
        title=title,
        initialdir=initialdir,
        initialfile=initialfile,
        filetypes=filetypes
    )
    
    dialog.wait_window()
    return dialog.result

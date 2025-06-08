"""
Utility functions for the P2P chat application.
Provides thread-safe GUI logging and other helper functions.
"""

import logging
import tkinter as tk
from typing import Callable, Any
from threading import current_thread
import asyncio
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def get_executable_dir() -> Path:
    """
    Get the directory where the executable is located.
    This works for both script execution and PyInstaller executables.
    
    Returns:
        Path: The directory containing the executable or script
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        executable_dir = Path(sys.executable).parent
    else:
        # Running as script
        executable_dir = Path(__file__).parent.parent.parent
    
    return executable_dir


def setup_logging(level: int = logging.INFO) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        level: Logging level (default: INFO)
    """
    # Get executable directory for log file
    executable_dir = get_executable_dir()
    log_file = executable_dir / "p2p_chat.log"
    
    # Configure logging to both file and console
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger.info(f"Logging initialized. Log file: {log_file}")


def log_to_tk(text_widget: tk.Text, message: str, tag: str = None) -> None:
    """
    Thread-safe function to append text to a Tkinter Text widget.
    
    Args:
        text_widget: The Tkinter Text widget to append to
        message: The message to append
        tag: Optional tag for text formatting
    """
    def append_text():
        try:
            text_widget.config(state=tk.NORMAL)
            text_widget.insert(tk.END, message + '\n')
            if tag:
                # Apply tag to the last line
                lines = int(text_widget.index(tk.END).split('.')[0]) - 1
                start_idx = f"{lines}.0"
                end_idx = f"{lines}.end"
                text_widget.tag_add(tag, start_idx, end_idx)
            text_widget.config(state=tk.DISABLED)
            text_widget.see(tk.END)
        except tk.TclError:
            # Widget might be destroyed
            pass
    
    # Execute in main thread if called from another thread
    try:
        if hasattr(text_widget, 'after'):
            text_widget.after(0, append_text)
        else:
            append_text()
    except Exception as e:
        logger.error(f"Failed to log to text widget: {e}")


def safe_call(func: Callable, *args, **kwargs) -> Any:
    """
    Safely call a function, catching and logging exceptions.
    
    Args:
        func: Function to call
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Function result or None if exception occurred
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error calling {func.__name__}: {e}")
        return None


def run_in_main_thread(root: tk.Tk, coro_func: Callable, *args, **kwargs) -> None:
    """
    Schedule a coroutine to run in the main thread's event loop.
    
    Args:
        root: Tkinter root window
        coro_func: Coroutine function to run
        *args: Positional arguments for the coroutine
        **kwargs: Keyword arguments for the coroutine
    """
    def schedule_coro():
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(coro_func(*args, **kwargs))
        except Exception as e:
            logger.error(f"Failed to schedule coroutine {coro_func.__name__}: {e}")
    
    root.after(0, schedule_coro)


class ColorCodes:
    """ANSI color codes for console output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    @classmethod
    def colored(cls, text: str, color: str) -> str:
        """Return colored text for console output."""
        return f"{color}{text}{cls.ENDC}" 
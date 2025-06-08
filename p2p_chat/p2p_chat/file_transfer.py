"""
File transfer management classes and utilities.
"""

import os
import hashlib
from typing import Optional


class FileTransfer:
    """Class to manage file transfer state and metadata."""
    
    def __init__(self, filename: str, file_size: int, checksum: str, transfer_id: str):
        self.filename = filename
        self.file_size = file_size
        self.checksum = checksum
        self.transfer_id = transfer_id
        self.bytes_received = 0
        self.chunks_received = []
        self.is_complete = False
        self.file_handle = None
        self.temp_path = None
        self.save_path = None  # Store user's chosen save location 
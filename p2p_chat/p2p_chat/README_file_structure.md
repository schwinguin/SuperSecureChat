# RTCPeer Module Structure

This directory contains the refactored RTCPeer module, split into multiple files for easier development and maintenance.

## File Structure

### Core Files

- **`rtc_peer.py`** - Main RTCPeer class with core WebRTC functionality
  - Connection establishment and management
  - Data channel setup and message handling
  - ICE gathering and signaling
  - Core WebRTC peer-to-peer communication

- **`file_transfer.py`** - FileTransfer class and utilities
  - FileTransfer state management class
  - File transfer metadata handling

- **`file_transfer_mixin.py`** - File transfer functionality mixin
  - All file transfer methods for RTCPeer
  - File control message handling
  - Binary data chunk processing
  - File sending/receiving logic
  - Transfer cleanup and error handling

## Usage

The split maintains full backward compatibility. Import and use RTCPeer as before:

```python
from p2p_chat.p2p_chat.rtc_peer import RTCPeer

# Create peer instance with all functionality
peer = RTCPeer()

# All methods are available including file transfer
peer.send_file("/path/to/file.txt")
peer.accept_file(transfer_id, "/save/directory")
```

## Benefits of the Split

1. **Separation of Concerns**: Core WebRTC logic is separate from file transfer logic
2. **Easier Maintenance**: Each file focuses on a specific aspect of functionality
3. **Better Organization**: Related functionality is grouped together
4. **Improved Readability**: Smaller, focused files are easier to understand
5. **Modular Design**: File transfer functionality can be reused or modified independently

## Dependencies

- `rtc_peer.py` depends on `file_transfer_mixin.py`
- `file_transfer_mixin.py` depends on `file_transfer.py`
- All security validations are handled through the existing `security.py` module 
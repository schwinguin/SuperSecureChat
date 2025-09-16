# SuperSecureChat

A modern peer-to-peer chat application using WebRTC for secure, end-to-end encrypted communication without servers. Features a beautiful modern GUI with dark/light themes, voice chat, file transfer, and comprehensive security features.

## Features

### 🔒 Security & Privacy
- **End-to-End Encryption**: WebRTC DTLS-SRTP encryption by default
- **No Central Server**: Direct peer-to-peer communication after connection
- **Manual Key Exchange**: Base64-encoded session descriptions prevent automated MITM attacks
- **Perfect Forward Secrecy**: Verification of PFS-enabled cipher suites
- **Input Sanitization**: Comprehensive message validation and sanitization
- **Security Monitoring**: Real-time security status logging

### 🎨 Modern User Interface
- **Ultra-Modern GUI**: Beautiful CustomTkinter interface with rounded corners and smooth animations
- **Dark/Light Themes**: Instant theme switching with system preference detection
- **Connection Wizard**: Step-by-step guided interface for creating and joining chats
- **Responsive Design**: Adapts to different window sizes with proper scaling
- **Visual Feedback**: Color-coded status indicators and confirmation messages

### 💬 Communication Features
- **Real-Time Messaging**: Instant encrypted text communication
- **Custom Usernames**: Optional chat names for personalized communication
- **Voice Chat**: Real-time P2P voice communication with simple toggle mode
- **File Transfer**: Secure file sharing with progress tracking and file dialogs
- **Audio Settings**: Configurable audio devices, sample rates, and buffer settings

### ⚙️ Advanced Configuration
- **Settings Management**: Persistent audio, GUI, and connection preferences
- **STUN Server Configuration**: Custom STUN servers for better connectivity
- **Reconnection Features**: Automatic reconnection with configurable retry logic
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Pre-built Releases**: Available releases for different platforms on the project page

## Security Enhancements (Latest)

### ✅ Updated Dependencies
- **aiortc 1.13.0+**: Latest version with security patches for recent CVEs
- Addresses vulnerabilities: CVE-2024-5493, CVE-2024-10488, CVE-2023-7024

### ✅ Input Sanitization
- **Message Validation**: Length limits, line count limits, control character filtering
- **Username Validation**: Maximum length, alphanumeric, spaces, dots, underscores, hyphens only, control character removal, pipe character replacement
- **Key Validation**: Base64 format verification, length validation, character validation
- **Security Violations**: Comprehensive error handling for malicious input

### ✅ Perfect Forward Secrecy Verification
- **Connection Security Monitoring**: Real-time DTLS state verification
- **PFS Validation**: Ensures forward secrecy is enabled per WebRTC standards
- **Security Status Logging**: Detailed connection security information

### ✅ Voice Chat Security
- **Encrypted Audio**: Voice data encrypted with WebRTC DTLS-SRTP
- **P2P Audio Streams**: Direct peer-to-peer audio without servers
- **Audio Input Control**: Push-to-talk and toggle modes for privacy

## Quick Start

## Requirements

- **Python 3.9 or higher**
- **Active internet connection** for STUN server (ICE negotiation)
- **NAT traversal capability** (most home networks work fine)
- **Audio system** (ALSA, PulseAudio, or JACK on Linux)

## Installation

### From Source

1. **Clone or download** the project
2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Using pip (if published)

```bash
pip install p2p-chat
```

## Usage

### Running the Application

```bash
# From source directory (recommended)
python -m p2p_chat

# With debug logging
python -m p2p_chat --debug


# If installed via pip
p2p-chat
```

### First Launch

When you first run SuperSecureChat, you'll see the modern welcome screen with the Connection Wizard:

1. **Welcome Screen**: Introduction to the app's features
2. **Username Entry**: Enter your display name (optional, defaults to "Anonymous")
3. **Connection Type**: Choose between creating or joining a chat
4. **Guided Process**: Step-by-step instructions for your chosen option

### Creating a Chat

1. Launch the application
2. **Welcome Screen**: Click "Next" to proceed
3. **Username**: Enter your display name (optional, defaults to "Anonymous")
4. **Connection Type**: Select "Create Chat"
5. **Create Chat**: Click "Create Chat" to generate an invite key
6. **Share Invite Key**: Copy and share the generated invite key with the other person
7. **Wait for Return Key**: Paste their return key when they send it back
8. **Connect**: Click "Connect" to establish the connection

### Joining a Chat

1. Launch the application
2. **Welcome Screen**: Click "Next" to proceed
3. **Username**: Enter your display name (optional, defaults to "Anonymous")
4. **Connection Type**: Select "Join Chat"
5. **Enter Invite Key**: Paste the invite key you received from the chat creator
6. **Join Chat**: Click "Join Chat" to generate your return key
7. **Share Return Key**: Copy and send your return key back to the chat creator
8. **Wait for Connection**: Wait for the creator to complete the handshake

### Chatting

Once connected:
- Type messages in the input field
- Press **Enter** or click **"Send"** to send messages
- Messages appear in different colors (blue for sent, green for received)
- Connection status is shown at the bottom

### Voice Chat

The application includes real-time voice communication capabilities:

#### Using Voice Chat
1. **After connecting** to a peer, click **"🎤 Start Voice Chat"** button
2. Grant microphone permissions when prompted by your system
3. The button will change to **"🔇 Stop Voice Chat"** and voice transmission will begin immediately
4. Click **"🔇 Stop Voice Chat"** to stop voice transmission

#### Voice Chat Features
- **Simple Toggle**: One-click start/stop voice transmission
- **Real-Time Audio**: Direct peer-to-peer voice communication
- **Audio Settings**: Configurable input/output devices and sample rates
- **Encrypted Audio**: Voice data encrypted with WebRTC DTLS-SRTP

#### Audio Quality
- **Sample Rate**: 48kHz for high-quality audio
- **Low Latency**: Optimized for real-time communication
- **Cross-Platform**: Works with ALSA, PulseAudio, and JACK on Linux

### File Transfer

The application supports secure file sharing between peers:

#### Sending Files
1. **After connecting** to a peer, click the **"📁 Send File"** button
2. Select the file you want to send using the file dialog
3. The recipient will receive a file transfer offer dialog
4. Monitor transfer progress in the progress dialog

#### Receiving Files
1. When a file transfer offer is received, a dialog will appear
2. Choose to **Accept** or **Reject** the file transfer
3. If accepting, choose where to save the file
4. Monitor transfer progress in the progress dialog

#### File Transfer Features
- **Secure Transfer**: Files are encrypted during transmission
- **Progress Tracking**: Real-time progress indicators
- **File Validation**: Checksums ensure file integrity
- **User Control**: Accept/reject file transfers
- **Modern Dialogs**: Beautiful file selection and progress dialogs

## How It Works

1. **WebRTC Setup**: Uses `aiortc` library for WebRTC peer connection
2. **STUN Server**: Employs Google's STUN server for NAT traversal
3. **Key Exchange**: Session descriptions are base64-encoded for manual sharing
4. **Data Channel**: Encrypted messages are sent via WebRTC data channels
5. **Audio Tracks**: Voice chat uses WebRTC audio tracks for real-time communication
6. **No Server**: Once connected, all communication is direct peer-to-peer

## Architecture

```
p2p_chat/
├── p2p_chat/                    # Main package
│   ├── __init__.py              # Package initialization
│   ├── __main__.py              # Module entry point
│   ├── main.py                  # Application orchestration & entry point
│   ├── modern_gui.py           # Modern GUI theme setup
│   ├── modern_chat_window.py    # Ultra-modern CustomTkinter GUI
│   ├── chat_window.py           # Legacy Tkinter GUI (fallback)
│   ├── connection_wizard.py     # Step-by-step connection wizard
│   ├── rtc_peer.py              # WebRTC peer connection wrapper
│   ├── file_transfer_mixin.py   # File transfer functionality
│   ├── voice_chat_mixin.py      # Voice chat functionality
│   ├── settings_manager.py     # Settings persistence
│   ├── audio_settings_dialog.py # Audio device configuration
│   ├── connection_settings_dialog.py # STUN server configuration
│   ├── file_transfer_dialog.py  # File transfer UI
│   ├── file_progress_dialog.py  # Transfer progress display
│   ├── custom_file_dialog.py    # Enhanced file dialogs
│   ├── security.py              # Input validation & sanitization
│   ├── signaling.py             # Base64 encoding/decoding helpers
│   └── utils.py                 # Utility functions
├── requirements.txt              # Dependencies
├── requirements-build.txt        # Build dependencies
├── pyproject.toml               # Project configuration
├── settings.json                # User settings
└── README.md                    # This file
```

## Pre-built Releases

SuperSecureChat is available as pre-built releases that don't require Python installation:

### Available Releases

Check the project page for the latest releases:
- **Image Release**: Portable image format for easy distribution
- **Windows Release**: Native Windows executable

**Features:**
- Single file with all dependencies included
- No Python installation required
- Self-contained settings and temporary files
- Cross-platform audio support


## Security Notes

- **WebRTC provides encryption** by default for data channels
- **Manual key exchange** prevents man-in-the-middle attacks during setup
- **No server involved** in actual communication after connection
- **STUN server** only used for NAT traversal, not for data

## Enhanced Security Features

### Input Validation & Sanitization
The application now includes comprehensive input validation:

```python
# Message sanitization
- Maximum message length: 8,192 characters
- Maximum lines per message: 100
- Control character filtering
- Empty message prevention

# Username sanitization
- Maximum username length: 50 characters
- Alphanumeric, spaces, dots, underscores, hyphens only
- Control character removal
- Pipe character replacement (prevents format conflicts)
- Empty usernames default to "Anonymous"

# Key validation  
- Base64 format verification
- Reasonable length bounds (50-10,000 chars)
- Character set validation
- Type checking
```

### Security Monitoring
Real-time security status monitoring provides:

```python
# Connection security information
- Connection state verification
- DTLS handshake status
- Perfect Forward Secrecy validation
- Security status logging
```

### Security Test Suite
Run the security test suite to verify all protections:

```bash
python test_security.py
```

### Security Violations
The application handles security violations gracefully:
- Invalid messages are rejected with clear error messages
- Malformed keys are detected and blocked
- Received messages are sanitized before display
- Security events are logged for monitoring

## Troubleshooting

### Connection Issues

- **Firewall**: Ensure your firewall allows the application
- **NAT/Router**: Most home routers work fine, but some corporate networks may block WebRTC
- **Internet**: Both peers need internet access for initial STUN negotiation

### Common Errors

- **"Failed to create chat"**: Check internet connection
- **"Connection failed"**: Usually NAT/firewall issue, try again or check network settings
- **"Invalid session description"**: Ensure you copied the complete key without truncation

## Dependencies

### Core Dependencies

- **aiortc>=1.13.0**: WebRTC implementation with latest security patches
- **pyee>=9.0**: Event handling system
- **sounddevice>=0.4.6**: Cross-platform audio I/O
- **numpy>=1.21.0**: Numerical computing for audio processing
- **customtkinter>=5.2.0**: Modern GUI framework
- **av>=10.0.0**: Audio/video processing

### Build Dependencies

- **pyinstaller**: For creating standalone executables
- **linuxdeploy**: For creating AppImage packages

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest tests/
```

### Code Formatting

```bash
# Format code
black p2p_chat/

# Check style
flake8 p2p_chat/

# Type checking
mypy p2p_chat/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Modern GUI Features

SuperSecureChat features a completely modernized user interface:

### 🎨 Visual Design
- **CustomTkinter Framework**: Modern, beautiful interface with rounded corners
- **Dark/Light Themes**: Instant theme switching with system preference detection
- **Smooth Animations**: Hover effects and state transitions
- **Professional Typography**: Custom fonts with proper weight and sizing
- **Color-Coded Elements**: Different colors for different actions and states

### 🧭 User Experience
- **Connection Wizard**: Step-by-step guided interface for creating and joining chats
- **Progress Indicators**: Visual step progress with color-coded status
- **Auto-copy Functionality**: Keys are automatically copied to clipboard
- **Visual Feedback**: Copy confirmations, loading states, and status indicators
- **Responsive Layout**: Adapts to different window sizes with proper scaling

### ⚙️ Settings & Configuration
- **Audio Settings Dialog**: Configure input/output devices, sample rates, and buffer settings
- **Connection Settings Dialog**: Custom STUN servers and connection parameters
- **Persistent Settings**: All preferences saved automatically
- **Settings Import/Export**: Backup and restore configuration

## Acknowledgments

- [aiortc](https://github.com/aiortc/aiortc) for WebRTC implementation
- [pyee](https://github.com/jfhbrook/pyee) for event handling
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern GUI framework
- [sounddevice](https://github.com/spatialaudio/python-sounddevice) for cross-platform audio
- Google STUN servers for NAT traversal 
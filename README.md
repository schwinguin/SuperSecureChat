# P2P Secure Chat

A peer-to-peer chat application using WebRTC for secure, end-to-end encrypted communication without servers.

## Features

- **End-to-End Encryption**: WebRTC DTLS-SRTP encryption by default
- **No Central Server**: Direct peer-to-peer communication after connection
- **Manual Key Exchange**: Base64-encoded session descriptions prevent automated MITM attacks
- **Custom Usernames**: Optional chat names for personalized communication
- **Voice Chat**: Real-time P2P voice communication with push-to-talk and toggle modes
- **File Transfer**: Secure file sharing with progress tracking and drag-and-drop support
- **Input Sanitization**: Comprehensive message validation and sanitization
- **Perfect Forward Secrecy**: Verification of PFS-enabled cipher suites
- **Security Monitoring**: Real-time security status logging
- **Cross-Platform**: Works on Windows, macOS, and Linux

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

- Python 3.9 or higher
- Active internet connection for STUN server (ICE negotiation)
- NAT traversal capability (most home networks work fine)

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
# From source directory
python -m p2p_chat

# Or with debug logging
python -m p2p_chat --debug

# If installed via pip
p2p-chat
```

### Creating a Chat

1. Launch the application
2. **Optional**: Enter your preferred chat name in the "Your Chat Name" field (leave empty for "Anonymous")
3. Click **"Create Chat"**
4. Copy the generated **invite key**
5. Share the invite key with the other person (via email, messaging, etc.)
6. Paste their **return key** when they send it back
7. Click **"Connect"** to establish the connection

### Joining a Chat

1. Launch the application
2. **Optional**: Enter your preferred chat name in the "Your Chat Name" field (leave empty for "Anonymous")
3. Click **"Join Chat"**
4. Paste the **invite key** you received
5. Click **"Join Chat"**
6. Copy the generated **return key**
7. Send the return key back to the chat creator
8. Wait for connection establishment

### Chatting

Once connected:
- Type messages in the input field
- Press **Enter** or click **"Send"** to send messages
- Messages appear in different colors (blue for sent, green for received)
- Connection status is shown at the bottom

### Voice Chat

The application now includes real-time voice communication capabilities:

#### Enabling Voice Chat
1. **After connecting** to a peer, click **"🎤 Enable Voice"** button
2. Grant microphone permissions when prompted by your browser/system
3. The voice status will show "Voice Chat: Enabled"

#### Using Voice Chat
- **Push-to-Talk Mode** (Default):
  - Hold down **"🗣️ Hold to Talk"** button while speaking
  - Or hold **Spacebar** (when not typing in text field)
  - Release to stop transmitting

- **Toggle Mode**:
  - Click **"🔄 Toggle Mode"** to start/stop continuous transmission
  - Useful for longer conversations without holding buttons

#### Voice Chat Controls
- **🎤 Enable/Disable Voice**: Turn voice chat on/off
- **🗣️ Hold to Talk**: Push-to-talk button (mouse or spacebar)
- **🔄 Toggle Mode**: Switch between push-to-talk and continuous modes
- **Voice Status**: Shows current voice chat state (Disabled/Enabled/Transmitting/Listening)

#### Audio Quality
- **Sample Rate**: 48kHz for high-quality audio
- **Low Latency**: Optimized for real-time communication
- **Automatic Gain**: Adjusts audio levels automatically
- **Echo Cancellation**: Built-in browser audio processing

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
├── p2p_chat/           # Main package
│   ├── __init__.py     # Package initialization
│   ├── main.py         # Application orchestration & entry point
│   ├── gui.py          # Tkinter GUI components
│   ├── rtc_peer.py     # WebRTC peer connection wrapper
│   ├── signaling.py    # Base64 encoding/decoding helpers
│   └── utils.py        # Utility functions
├── requirements.txt    # Dependencies
├── pyproject.toml      # Project configuration
└── README.md          # This file
```

## Building Standalone Executables

### Using PyInstaller

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --windowed --name "P2P Chat" -p p2p_chat p2p_chat/main.py

# The executable will be in dist/
```

### Using cx_Freeze

```bash
pip install cx_freeze
python setup.py build
```

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

## Acknowledgments

- [aiortc](https://github.com/aiortc/aiortc) for WebRTC implementation
- [pyee](https://github.com/jfhbrook/pyee) for event handling
- Google STUN servers for NAT traversal 
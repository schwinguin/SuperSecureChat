# SuperSecureChat - Linux Executable

## Overview

SuperSecureChat is a secure peer-to-peer chat application with voice communication and file transfer capabilities. This is a single-file Linux executable that includes all dependencies and creates all necessary files in its own directory.

## Features

- **Secure P2P Communication**: End-to-end encrypted messaging using WebRTC
- **Voice Chat**: Real-time voice communication with audio device selection
- **File Transfer**: Secure file sharing between peers
- **Cross-Platform Audio**: Works with ALSA, PulseAudio, and other Linux audio systems
- **Portable**: Single executable file with no external dependencies
- **Self-Contained**: All settings, logs, and temporary files created in executable directory

## System Requirements

- **Operating System**: Linux (64-bit)
- **Architecture**: x86_64 (Intel/AMD 64-bit)
- **Audio System**: ALSA, PulseAudio, or JACK
- **Network**: Internet connection for P2P communication
- **Permissions**: Execute permission for the binary

## Installation & Usage

### Quick Start

1. **Download/Copy** the `SuperSecureChat` executable to your desired directory
2. **Make it executable**:
   ```bash
   chmod +x SuperSecureChat
   ```
3. **Run the application**:
   ```bash
   ./SuperSecureChat
   ```

### File Management

The application creates the following files in the same directory as the executable:

- `settings.json` - Application settings (audio devices, GUI preferences)
- `p2p_transfer_*` - Temporary files during file transfers (auto-cleaned)

**Note:** For security reasons, the application does not create log files. All logging output goes to the console only.

### Audio Setup

The application automatically detects available audio devices. To configure:

1. Open the application
2. Go to **Settings** → **Audio Settings**
3. Select your preferred input/output devices
4. Adjust sample rate and buffer settings if needed

## Cross-Platform Compatibility

### Audio System Support

✅ **Linux Audio Systems**:
- ALSA (Advanced Linux Sound Architecture)
- PulseAudio
- JACK Audio Connection Kit
- OSS (Open Sound System)

✅ **Windows Audio Systems** (if running via compatibility layer):
- DirectSound
- WASAPI
- MME (Windows Multimedia Extensions)

### Network Compatibility

- **IPv4/IPv6**: Full support for both protocols
- **NAT Traversal**: Automatic NAT/firewall traversal using STUN/TURN
- **Firewall Friendly**: Uses standard WebRTC protocols

## Technical Details

### Dependencies Included

The executable includes all necessary dependencies:

- **Python 3.12 Runtime**: Complete Python interpreter
- **WebRTC Libraries**: aiortc for peer-to-peer communication
- **Audio Libraries**: sounddevice + PortAudio for cross-platform audio
- **GUI Framework**: CustomTkinter for modern interface
- **Cryptography**: End-to-end encryption libraries
- **Media Codecs**: Audio/video processing libraries

### Security Features

- **End-to-End Encryption**: All communication encrypted using WebRTC DTLS
- **File Integrity**: SHA-256 checksums for file transfers
- **Input Validation**: Sanitized file names and message content
- **Memory Safety**: Secure handling of sensitive data

### Performance

- **Executable Size**: ~72MB (includes complete runtime)
- **Memory Usage**: ~50-100MB during operation
- **CPU Usage**: Low impact, optimized for real-time communication
- **Network Usage**: Minimal overhead, direct P2P connections

## Troubleshooting

### Audio Issues

**No audio devices detected**:
```bash
# Check if audio system is running
pulseaudio --check -v
# or for ALSA
aplay -l
```

**Permission denied for audio**:
```bash
# Add user to audio group
sudo usermod -a -G audio $USER
# Logout and login again
```

### Network Issues

**Cannot connect to peer**:
- Check firewall settings
- Ensure internet connection
- Try different network (mobile hotspot)

**Connection drops frequently**:
- Check network stability
- Disable VPN if active
- Try different STUN/TURN servers

### Application Issues

**Executable won't start**:
```bash
# Check if executable
ls -la SuperSecureChat
# Make executable if needed
chmod +x SuperSecureChat
```

**Missing libraries error**:
```bash
# Check system libraries
ldd SuperSecureChat
# Install missing system libraries if any
```

### Console Output Analysis

For security reasons, no log files are created. Check the console output for detailed error information when running the application from a terminal.

## Building from Source

If you want to build the executable yourself:

1. **Clone the repository**
2. **Set up virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```
4. **Run build script**:
   ```bash
   ./build_linux_executable.sh
   ```

## Support

For issues, feature requests, or contributions, please refer to the main project repository.

## License

This application is distributed under the same license as the source code. See the main project for license details.

---

**Note**: This executable is self-contained and portable. You can copy it to any Linux system and run it without installing additional dependencies. 
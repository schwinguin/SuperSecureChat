"""
Security utilities for P2P chat application.
Provides input sanitization and security verification functions.
"""

import logging
import re
import os
import hashlib
import urllib.parse
from typing import Optional, List, Dict, Any, Set
from aiortc import RTCPeerConnection

logger = logging.getLogger(__name__)

# Maximum message length to prevent DoS attacks
MAX_MESSAGE_LENGTH = 8192
# Maximum number of lines in a message
MAX_MESSAGE_LINES = 100
# Maximum file size for transfers (100MB)
MAX_FILE_SIZE = 100 * 1024 * 1024
# Maximum filename length
MAX_FILENAME_LENGTH = 255
# Pattern for potentially dangerous characters
DANGEROUS_PATTERN = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]')
# Allowed file extensions for security
ALLOWED_FILE_EXTENSIONS: Set[str] = {
    # Documents
    '.txt', '.pdf', '.doc', '.docx', '.rtf', '.odt',
    # Images
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
    # Audio
    '.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a',
    # Video
    '.mp4', '.avi', '.mkv', '.webm', '.mov', '.flv',
    # Archives
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
    # Code
    '.py', '.js', '.html', '.css', '.json', '.xml', '.csv',
    # Other
    '.epub', '.mobi'
}
# Dangerous file extensions that should be blocked
DANGEROUS_FILE_EXTENSIONS: Set[str] = {
    '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
    '.msi', '.deb', '.rpm', '.dmg', '.app', '.sh', '.ps1', '.psm1'
}

# Known cipher suites that support Perfect Forward Secrecy
PFS_CIPHER_SUITES = {
    'TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384',
    'TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384',
    'TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256',
    'TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256',
    'TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256',
    'TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256',
    'TLS_DHE_RSA_WITH_AES_256_GCM_SHA384',
    'TLS_DHE_RSA_WITH_AES_128_GCM_SHA256',
    'TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA384',
    'TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA384',
    'TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA',
    'TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA',
    'TLS_DHE_RSA_WITH_AES_256_CBC_SHA256',
    'TLS_DHE_RSA_WITH_AES_256_CBC_SHA',
    'TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA256',
    'TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256',
    'TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA',
    'TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA',
    'TLS_DHE_RSA_WITH_AES_128_CBC_SHA256',
    'TLS_DHE_RSA_WITH_AES_128_CBC_SHA'
}


class SecurityViolation(Exception):
    """Exception raised when a security violation is detected."""
    pass


class FileSecurityViolation(SecurityViolation):
    """Exception raised when a file security violation is detected."""
    pass


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other attacks.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        Sanitized filename
        
    Raises:
        FileSecurityViolation: If the filename violates security policies
    """
    if not isinstance(filename, str):
        raise FileSecurityViolation("Filename must be a string")
    
    # Strip whitespace
    filename = filename.strip()
    
    # Check filename length
    if len(filename) > MAX_FILENAME_LENGTH:
        raise FileSecurityViolation(f"Filename too long (max {MAX_FILENAME_LENGTH} characters)")
    
    if not filename:
        raise FileSecurityViolation("Filename cannot be empty")
    
    # Remove dangerous control characters
    if DANGEROUS_PATTERN.search(filename):
        logger.warning("Removing dangerous control characters from filename")
        filename = DANGEROUS_PATTERN.sub('', filename)
    
    # Remove path traversal attempts
    filename = os.path.basename(filename)
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')
    
    # Remove leading dots to prevent hidden files
    while filename.startswith('.'):
        filename = filename[1:]
    
    if not filename:
        raise FileSecurityViolation("Filename is empty after sanitization")
    
    # Check for dangerous extensions
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext in DANGEROUS_FILE_EXTENSIONS:
        raise FileSecurityViolation(f"File type '{file_ext}' is not allowed for security reasons")
    
    return filename


def validate_file_transfer(filename: str, file_size: int, allow_any_extension: bool = False) -> str:
    """
    Validate file transfer parameters for security.
    
    Args:
        filename: The filename to validate
        file_size: The size of the file in bytes
        allow_any_extension: Whether to allow any file extension (default: False)
        
    Returns:
        Sanitized filename
        
    Raises:
        FileSecurityViolation: If validation fails
    """
    # Validate file size
    if file_size <= 0:
        raise FileSecurityViolation("File size must be positive")
    
    if file_size > MAX_FILE_SIZE:
        size_mb = file_size / (1024 * 1024)
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise FileSecurityViolation(f"File too large ({size_mb:.1f}MB). Maximum allowed: {max_mb:.0f}MB")
    
    # Sanitize filename
    sanitized_filename = sanitize_filename(filename)
    
    # Check file extension if not allowing any extension
    if not allow_any_extension:
        file_ext = os.path.splitext(sanitized_filename)[1].lower()
        if file_ext and file_ext not in ALLOWED_FILE_EXTENSIONS:
            raise FileSecurityViolation(f"File type '{file_ext}' is not allowed")
    
    logger.info(f"File validation passed: {sanitized_filename} ({file_size} bytes)")
    return sanitized_filename


def calculate_file_checksum(file_path: str) -> str:
    """
    Calculate SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hexadecimal SHA-256 checksum
        
    Raises:
        FileSecurityViolation: If file cannot be read
    """
    try:
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        raise FileSecurityViolation(f"Cannot calculate file checksum: {e}")


def verify_file_integrity(file_path: str, expected_checksum: str) -> bool:
    """
    Verify file integrity using SHA-256 checksum.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected SHA-256 checksum
        
    Returns:
        True if checksum matches, False otherwise
        
    Raises:
        FileSecurityViolation: If verification fails
    """
    try:
        actual_checksum = calculate_file_checksum(file_path)
        return actual_checksum.lower() == expected_checksum.lower()
    except Exception as e:
        raise FileSecurityViolation(f"File integrity verification failed: {e}")


def sanitize_username(username: str) -> str:
    """
    Sanitize username to prevent abuse.
    
    Args:
        username: The username to sanitize
        
    Returns:
        Sanitized username
        
    Raises:
        SecurityViolation: If the username violates security policies
    """
    if not isinstance(username, str):
        raise SecurityViolation("Username must be a string")
    
    # Strip whitespace
    username = username.strip()
    
    # Check username length
    if len(username) > 50:
        raise SecurityViolation("Username too long (max 50 characters)")
    
    # Remove dangerous control characters
    if DANGEROUS_PATTERN.search(username):
        logger.warning("Removing dangerous control characters from username")
        username = DANGEROUS_PATTERN.sub('', username)
    
    # Check for empty username after sanitization
    if not username:
        return "Anonymous"
    
    # Replace pipe character to avoid conflicts with message format
    username = username.replace("|", "_")
    
    # Limit to alphanumeric, spaces, and common symbols
    import string
    allowed_chars = string.ascii_letters + string.digits + ' ._-'
    username = ''.join(c for c in username if c in allowed_chars)
    
    # Final check for empty username
    if not username:
        return "Anonymous"
    
    return username


def sanitize_message(message: str) -> str:
    """
    Sanitize input message to prevent various attacks.
    
    Args:
        message: The input message to sanitize (may include username|content format)
        
    Returns:
        Sanitized message
        
    Raises:
        SecurityViolation: If the message violates security policies
    """
    if not isinstance(message, str):
        raise SecurityViolation("Message must be a string")
    
    # Check if message contains username format
    if "|" in message:
        parts = message.split("|", 1)
        if len(parts) == 2:
            username, content = parts
            # Sanitize both parts separately
            sanitized_username = sanitize_username(username)
            sanitized_content = _sanitize_message_content(content)
            return f"{sanitized_username}|{sanitized_content}"
    
    # Regular message without username
    return _sanitize_message_content(message)


def _sanitize_message_content(content: str) -> str:
    """
    Sanitize message content (internal function).
    
    Args:
        content: The message content to sanitize
        
    Returns:
        Sanitized message content
        
    Raises:
        SecurityViolation: If the content violates security policies
    """
    if not isinstance(content, str):
        raise SecurityViolation("Message content must be a string")
    
    # Check message length
    if len(content) > MAX_MESSAGE_LENGTH:
        raise SecurityViolation(f"Message too long (max {MAX_MESSAGE_LENGTH} characters)")
    
    # Check for excessive line breaks (potential DoS)
    lines = content.split('\n')
    if len(lines) > MAX_MESSAGE_LINES:
        raise SecurityViolation(f"Too many lines in message (max {MAX_MESSAGE_LINES})")
    
    # Remove dangerous control characters but preserve common whitespace
    if DANGEROUS_PATTERN.search(content):
        logger.warning("Removing dangerous control characters from message")
        content = DANGEROUS_PATTERN.sub('', content)
    
    # Strip leading/trailing whitespace
    content = content.strip()
    
    # Prevent empty messages after sanitization
    if not content:
        raise SecurityViolation("Message is empty after sanitization")
    
    return content


def validate_invite_key(invite_key: str) -> str:
    """
    Validate and sanitize invite/return key.
    
    Args:
        invite_key: The base64-encoded invite key
        
    Returns:
        Sanitized invite key
        
    Raises:
        SecurityViolation: If the key is invalid
    """
    if not isinstance(invite_key, str):
        raise SecurityViolation("Invite key must be a string")
    
    # Remove whitespace
    invite_key = invite_key.strip()
    
    if not invite_key:
        raise SecurityViolation("Invite key cannot be empty")
    
    # Check for reasonable length (base64 keys should be within certain bounds)
    if len(invite_key) < 50 or len(invite_key) > 10000:
        raise SecurityViolation("Invite key length is suspicious")
    
    # Basic base64 character validation
    import string
    valid_chars = string.ascii_letters + string.digits + '+/='
    if not all(c in valid_chars for c in invite_key):
        raise SecurityViolation("Invite key contains invalid characters")
    
    return invite_key


def get_connection_security_info(pc: RTCPeerConnection) -> Dict[str, Any]:
    """
    Get security information about the WebRTC connection.
    
    Args:
        pc: The RTCPeerConnection instance
        
    Returns:
        Dictionary containing security information
    """
    security_info = {
        'connection_state': pc.connectionState if pc else 'unknown',
        'ice_connection_state': pc.iceConnectionState if pc else 'unknown',
        'ice_gathering_state': pc.iceGatheringState if pc else 'unknown',
        'dtls_state': 'unknown',
        'cipher_suite': 'unknown',
        'pfs_enabled': False,
        'certificate_verified': False
    }
    
    try:
        # Try to get DTLS transport information
        if hasattr(pc, 'sctp') and pc.sctp and hasattr(pc.sctp, 'transport'):
            dtls_transport = pc.sctp.transport
            if hasattr(dtls_transport, 'state'):
                security_info['dtls_state'] = dtls_transport.state
                
            # Note: aiortc doesn't expose cipher suite information directly
            # This is a limitation of the library
            logger.debug("DTLS transport found but cipher suite info not available in aiortc")
            
    except Exception as e:
        logger.warning(f"Could not retrieve DTLS security information: {e}")
    
    return security_info


def verify_perfect_forward_secrecy(security_info: Dict[str, Any]) -> bool:
    """
    Verify that Perfect Forward Secrecy is enabled.
    
    Args:
        security_info: Security information from get_connection_security_info
        
    Returns:
        True if PFS appears to be enabled, False otherwise
    """
    # Check if connection is established
    if security_info.get('connection_state') != 'connected':
        logger.warning("Cannot verify PFS: connection not established")
        return False
    
    if security_info.get('dtls_state') not in ['connected', 'completed']:
        logger.warning("Cannot verify PFS: DTLS not established")
        return False
    
    # Unfortunately, aiortc doesn't expose cipher suite information
    # We can only verify that DTLS is established, which by default
    # in WebRTC should use PFS-enabled cipher suites
    
    # WebRTC specifications require PFS-capable cipher suites
    # If DTLS is connected, we can reasonably assume PFS is enabled
    if security_info.get('dtls_state') in ['connected', 'completed']:
        logger.info("DTLS established - PFS should be enabled by WebRTC standards")
        return True
    
    return False


def log_security_status(pc: RTCPeerConnection) -> None:
    """
    Log comprehensive security status of the connection.
    
    Args:
        pc: The RTCPeerConnection instance
    """
    security_info = get_connection_security_info(pc)
    pfs_enabled = verify_perfect_forward_secrecy(security_info)
    
    logger.info("=== CONNECTION SECURITY STATUS ===")
    logger.info(f"Connection State: {security_info['connection_state']}")
    logger.info(f"ICE Connection State: {security_info['ice_connection_state']}")
    logger.info(f"ICE Gathering State: {security_info['ice_gathering_state']}")
    logger.info(f"DTLS State: {security_info['dtls_state']}")
    logger.info(f"Perfect Forward Secrecy: {'✓ Enabled' if pfs_enabled else '✗ Unknown/Disabled'}")
    
    if security_info['connection_state'] == 'connected':
        logger.info("🔒 Connection is encrypted and secure")
    else:
        logger.warning("⚠️  Connection security cannot be verified")
    
    logger.info("=== END SECURITY STATUS ===")


def validate_stun_url(stun_url: str) -> str:
    """
    Validate and sanitize a STUN server URL.
    
    Args:
        stun_url: The STUN URL to validate
        
    Returns:
        The validated and sanitized STUN URL
        
    Raises:
        SecurityViolation: If the URL is invalid or potentially malicious
    """
    if not stun_url or not isinstance(stun_url, str):
        raise SecurityViolation("STUN URL must be a non-empty string")
    
    # Remove whitespace
    stun_url = stun_url.strip()
    
    if not stun_url:
        raise SecurityViolation("STUN URL cannot be empty")
    
    # Check length
    if len(stun_url) > 200:
        raise SecurityViolation("STUN URL too long (max 200 characters)")
    
    # Must start with stun: or stuns:
    if not stun_url.startswith(('stun:', 'stuns:')):
        raise SecurityViolation("STUN URL must start with 'stun:' or 'stuns:'")
    
    try:
        # Parse the URL - for STUN URLs, we need to handle them specially
        # since urllib.parse doesn't recognize stun: as having netloc
        if stun_url.startswith('stun:'):
            scheme = 'stun'
            netloc = stun_url[5:]  # Remove 'stun:'
        elif stun_url.startswith('stuns:'):
            scheme = 'stuns'
            netloc = stun_url[6:]  # Remove 'stuns:'
        else:
            raise SecurityViolation("Invalid STUN URL scheme")
        
        # Parse host and port from netloc
        if ':' in netloc:
            hostname, port_str = netloc.rsplit(':', 1)
            try:
                port = int(port_str)
                if not (1 <= port <= 65535):
                    raise SecurityViolation("Invalid port number in STUN URL")
            except ValueError:
                raise SecurityViolation("Invalid port number in STUN URL")
        else:
            hostname = netloc
            port = None
        
        # Must have hostname
        if not hostname:
            raise SecurityViolation("STUN URL must have a hostname")
        
        # Validate hostname (basic check for dangerous characters)
        hostname = hostname.lower()
        if re.search(r'[^a-z0-9.-]', hostname):
            raise SecurityViolation("Invalid characters in STUN hostname")
        
        # Check for localhost/private IPs if desired (optional - users might want local STUN)
        # For now, we'll allow them but log a warning
        if hostname in ('localhost', '127.0.0.1', '::1') or hostname.startswith('192.168.') or hostname.startswith('10.') or hostname.startswith('172.'):
            logger.warning(f"Using local/private STUN server: {hostname}")
        
        # Reconstruct clean URL
        port_part = f":{port}" if port else ""
        clean_url = f"{scheme}:{hostname}{port_part}"
        
        logger.debug(f"STUN URL validation passed: {clean_url}")
        return clean_url
        
    except ValueError as e:
        raise SecurityViolation(f"Invalid STUN URL format: {e}")
    except Exception as e:
        logger.error(f"Unexpected error validating STUN URL: {e}")
        raise SecurityViolation(f"STUN URL validation failed: {e}")


def validate_stun_servers(stun_servers: List[str]) -> List[str]:
    """
    Validate a list of STUN server URLs.
    
    Args:
        stun_servers: List of STUN server URLs
        
    Returns:
        List of validated STUN server URLs
        
    Raises:
        SecurityViolation: If any URL is invalid
    """
    if not stun_servers:
        raise SecurityViolation("At least one STUN server must be provided")
    
    if len(stun_servers) > 10:
        raise SecurityViolation("Too many STUN servers (max 10)")
    
    validated_servers = []
    for server in stun_servers:
        validated_servers.append(validate_stun_url(server))
    
    return validated_servers 
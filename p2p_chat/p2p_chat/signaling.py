"""
Signaling helpers for WebRTC peer-to-peer connection establishment.
Handles base64 encoding/decoding of session descriptions for manual key exchange.
"""

import base64
import json
import logging
from typing import Dict, Any
from aiortc import RTCSessionDescription

logger = logging.getLogger(__name__)


def encode(description: RTCSessionDescription) -> str:
    """
    Encode an RTCSessionDescription to a base64 string for manual sharing.
    
    Args:
        description: The RTCSessionDescription to encode
        
    Returns:
        Base64-encoded string containing the session description
    """
    try:
        data = {
            "type": description.type,
            "sdp": description.sdp
        }
        json_str = json.dumps(data, separators=(',', ':'))
        encoded = base64.b64encode(json_str.encode('utf-8')).decode('ascii')
        logger.debug(f"Encoded {description.type} description to {len(encoded)} chars")
        return encoded
    except Exception as e:
        logger.error(f"Failed to encode session description: {e}")
        raise


def decode(key: str) -> Dict[str, Any]:
    """
    Decode a base64 string back into session description data.
    
    Args:
        key: Base64-encoded session description string
        
    Returns:
        Dictionary with 'type' and 'sdp' keys for RTCSessionDescription creation
        
    Raises:
        ValueError: If the key cannot be decoded or parsed
    """
    try:
        # Remove any whitespace
        key = key.strip()
        
        # Decode base64
        json_str = base64.b64decode(key.encode('ascii')).decode('utf-8')
        
        # Parse JSON
        data = json.loads(json_str)
        
        # Validate required fields
        if not isinstance(data, dict) or 'type' not in data or 'sdp' not in data:
            raise ValueError("Invalid session description format")
            
        logger.debug(f"Decoded {data['type']} description from {len(key)} chars")
        return data
        
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.error(f"Failed to decode session description: {e}")
        raise ValueError(f"Invalid session description key: {e}")
    except Exception as e:
        logger.error(f"Unexpected error decoding session description: {e}")
        raise 
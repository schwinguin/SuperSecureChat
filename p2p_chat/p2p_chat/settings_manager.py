"""
Settings Manager for the P2P chat application.
Handles loading and saving user preferences including audio settings.
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from .utils import get_executable_dir

logger = logging.getLogger(__name__)


class SettingsManager:
    """
    Manages application settings persistence.
    Saves settings to a JSON file in the executable directory.
    """
    
    def __init__(self, app_name: str = "p2p_chat"):
        self.app_name = app_name
        self.settings_dir = get_executable_dir()
        self.settings_file = self.settings_dir / "settings.json"
        
        # Default settings
        self.default_settings = {
            "audio": {
                "input_device": None,
                "input_device_name": "Default",
                "output_device": None,
                "output_device_name": "Default",
                "sample_rate": 48000,
                "channels": 1,
                "frames_per_buffer": 1024
            },
            "gui": {
                "theme": "dark",
                "window_geometry": "900x700"
            },
            "connection": {
                "max_reconnection_attempts": 5,
                "initial_reconnection_delay": 2.0,
                "max_reconnection_delay": 30.0,
                "connection_timeout": 15.0,
                "heartbeat_interval": 1.0,
                "stun_servers": [
                    "stun:stun.l.google.com:19302",
                    "stun:stun.stunprotocol.org:3478",
                    "stun:stun1.l.google.com:19302",
                    "stun:stun2.l.google.com:19302"
                ],
                "custom_stun_server": "",
                "use_custom_stun": False
            }
        }
        
        self.settings = self.default_settings.copy()
        self._ensure_settings_dir()
        
    def _ensure_settings_dir(self):
        """Ensure the settings directory exists."""
        try:
            self.settings_dir.mkdir(exist_ok=True)
            logger.debug(f"Settings directory: {self.settings_dir}")
        except Exception as e:
            logger.error(f"Failed to create settings directory: {e}")
            
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                self.settings = self._merge_settings(self.default_settings, loaded_settings)
                logger.info(f"Settings loaded from {self.settings_file}")
            else:
                logger.info("No settings file found, using defaults")
                self.settings = self.default_settings.copy()
                
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            self.settings = self.default_settings.copy()
            
        return self.settings
    
    def save_settings(self, settings: Optional[Dict[str, Any]] = None):
        """Save settings to file."""
        try:
            settings_to_save = settings or self.settings
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_to_save, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Settings saved to {self.settings_file}")
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            
    def get_audio_settings(self) -> Dict[str, Any]:
        """Get audio-specific settings."""
        return self.settings.get("audio", self.default_settings["audio"]).copy()
    
    def update_audio_settings(self, audio_settings: Dict[str, Any]):
        """Update audio settings and save."""
        if "audio" not in self.settings:
            self.settings["audio"] = {}
            
        self.settings["audio"].update(audio_settings)
        self.save_settings()
        logger.info(f"Audio settings updated: {audio_settings}")
        
    def get_gui_settings(self) -> Dict[str, Any]:
        """Get GUI-specific settings."""
        return self.settings.get("gui", self.default_settings["gui"]).copy()
    
    def update_gui_settings(self, gui_settings: Dict[str, Any]):
        """Update GUI settings and save."""
        if "gui" not in self.settings:
            self.settings["gui"] = {}
            
        self.settings["gui"].update(gui_settings)
        self.save_settings()
        logger.info(f"GUI settings updated: {gui_settings}")
        
    def get_connection_settings(self) -> Dict[str, Any]:
        """Get connection-specific settings."""
        return self.settings.get("connection", self.default_settings["connection"]).copy()
    
    def update_connection_settings(self, connection_settings: Dict[str, Any]):
        """Update connection settings and save."""
        if "connection" not in self.settings:
            self.settings["connection"] = {}
            
        self.settings["connection"].update(connection_settings)
        self.save_settings()
        logger.info(f"Connection settings updated: {connection_settings}")
        
    def _merge_settings(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded settings with defaults to ensure all keys exist."""
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self.settings = self.default_settings.copy()
        self.save_settings()
        logger.info("Settings reset to defaults")
        
    def get_setting(self, key_path: str, default=None):
        """Get a specific setting using dot notation (e.g., 'audio.sample_rate')."""
        keys = key_path.split('.')
        value = self.settings
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
            
    def set_setting(self, key_path: str, value: Any):
        """Set a specific setting using dot notation (e.g., 'audio.sample_rate')."""
        keys = key_path.split('.')
        settings = self.settings
        
        # Navigate to the parent dictionary
        for key in keys[:-1]:
            if key not in settings:
                settings[key] = {}
            settings = settings[key]
            
        # Set the value
        settings[keys[-1]] = value
        self.save_settings()
        logger.debug(f"Setting {key_path} = {value}")
        
    def export_settings(self, file_path: str):
        """Export settings to a specific file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            logger.info(f"Settings exported to {file_path}")
        except Exception as e:
            logger.error(f"Failed to export settings: {e}")
            raise
            
    def import_settings(self, file_path: str):
        """Import settings from a specific file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
                
            self.settings = self._merge_settings(self.default_settings, imported_settings)
            self.save_settings()
            logger.info(f"Settings imported from {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
            raise 
"""
Audio Settings Dialog for the P2P chat application.
Allows users to configure input and output audio devices.
"""

import customtkinter as ctk
from tkinter import messagebox
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    sd = None
import logging
from typing import Optional, Dict, Any, Callable

logger = logging.getLogger(__name__)


class AudioSettingsDialog:
    """
    Dialog for configuring audio input and output devices.
    Shows available audio devices and allows user to select preferred ones.
    """
    
    def __init__(self, parent: ctk.CTk, current_settings: Dict[str, Any] = None):
        self.parent = parent
        self.dialog: Optional[ctk.CTkToplevel] = None
        self.current_settings = current_settings or {}
        
        # Audio device lists
        self.input_devices = []
        self.output_devices = []
        
        # Selected devices
        self.selected_input_device = self.current_settings.get('input_device', None)
        self.selected_output_device = self.current_settings.get('output_device', None)
        
        # UI elements
        self.input_dropdown: Optional[ctk.CTkComboBox] = None
        self.output_dropdown: Optional[ctk.CTkComboBox] = None
        self.test_input_button: Optional[ctk.CTkButton] = None
        self.test_output_button: Optional[ctk.CTkButton] = None
        
        # Callback for when settings are saved
        self.on_settings_saved: Optional[Callable] = None
        
    def show(self):
        """Show the audio settings dialog."""
        self._create_dialog()
        self._load_audio_devices()
        self._setup_ui()
        
    def _create_dialog(self):
        """Create the dialog window."""
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("🎵 Audio Settings")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        
        # Make dialog modal - but safely
        self.dialog.transient(self.parent)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")
        
        # Configure grid
        self.dialog.grid_columnconfigure(0, weight=1)
        self.dialog.grid_rowconfigure(0, weight=1)
        
        # Set grab after dialog is properly displayed
        self.dialog.after(100, self._safe_grab_set)
        
    def _safe_grab_set(self):
        """Safely set grab on the dialog."""
        try:
            if self.dialog and self.dialog.winfo_exists():
                self.dialog.grab_set()
        except Exception as e:
            logger.debug(f"Could not set grab on dialog: {e}")
        
    def _load_audio_devices(self):
        """Load available audio devices."""
        if not SOUNDDEVICE_AVAILABLE:
            logger.warning("Sounddevice not available, using default devices")
            self.input_devices = [{'index': 0, 'name': 'Default Input', 'hostapi': 0, 'max_input_channels': 1, 'max_output_channels': 0, 'default_samplerate': 44100}]
            self.output_devices = [{'index': 0, 'name': 'Default Output', 'hostapi': 0, 'max_input_channels': 0, 'max_output_channels': 1, 'default_samplerate': 44100}]
            return
            
        try:
            devices = sd.query_devices()
            
            # Clear device lists
            self.input_devices = []
            self.output_devices = []
            
            # Populate device lists
            for i, device in enumerate(devices):
                device_info = {
                    'index': i,
                    'name': device['name'],
                    'hostapi': device['hostapi'],
                    'max_input_channels': device['max_input_channels'],
                    'max_output_channels': device['max_output_channels'],
                    'default_samplerate': device['default_samplerate']
                }
                
                if device['max_input_channels'] > 0:
                    self.input_devices.append(device_info)
                    
                if device['max_output_channels'] > 0:
                    self.output_devices.append(device_info)
                    
            logger.info(f"Found {len(self.input_devices)} input devices and {len(self.output_devices)} output devices")
            
        except Exception as e:
            logger.error(f"Failed to load audio devices: {e}")
            messagebox.showerror("Error", f"Failed to load audio devices: {e}")
            
    def _setup_ui(self):
        """Set up the dialog UI."""
        # Main container
        main_frame = ctk.CTkFrame(self.dialog, corner_radius=0)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="🎵 Audio Device Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(20, 30))
        
        # Input device section
        input_frame = ctk.CTkFrame(main_frame, corner_radius=0)
        input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))
        input_frame.grid_columnconfigure(1, weight=1)
        
        input_label = ctk.CTkLabel(
            input_frame,
            text="🎤 Input Device:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        input_label.grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        # Input device dropdown
        input_device_names = [f"{dev['name']}" for dev in self.input_devices]
        if not input_device_names:
            input_device_names = ["No input devices found"]
            
        self.input_dropdown = ctk.CTkComboBox(
            input_frame,
            values=input_device_names,
            state="readonly" if input_device_names[0] != "No input devices found" else "disabled",
            width=250
        )
        self.input_dropdown.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="ew")
        
        # Set current selection
        if self.selected_input_device is not None:
            try:
                current_name = next(dev['name'] for dev in self.input_devices if dev['index'] == self.selected_input_device)
                self.input_dropdown.set(current_name)
            except StopIteration:
                pass
        elif input_device_names and input_device_names[0] != "No input devices found":
            self.input_dropdown.set(input_device_names[0])
            
        # Test input button
        self.test_input_button = ctk.CTkButton(
            input_frame,
            text="🔊 Test",
            width=80,
            command=self._test_input_device,
            corner_radius=8,
            state="normal" if input_device_names[0] != "No input devices found" else "disabled"
        )
        self.test_input_button.grid(row=0, column=2, padx=(0, 15), pady=15)
        
        # Output device section
        output_frame = ctk.CTkFrame(main_frame, corner_radius=0)
        output_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        output_frame.grid_columnconfigure(1, weight=1)
        
        output_label = ctk.CTkLabel(
            output_frame,
            text="🔊 Output Device:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        output_label.grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        # Output device dropdown
        output_device_names = [f"{dev['name']}" for dev in self.output_devices]
        if not output_device_names:
            output_device_names = ["No output devices found"]
            
        self.output_dropdown = ctk.CTkComboBox(
            output_frame,
            values=output_device_names,
            state="readonly" if output_device_names[0] != "No output devices found" else "disabled",
            width=250
        )
        self.output_dropdown.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="ew")
        
        # Set current selection
        if self.selected_output_device is not None:
            try:
                current_name = next(dev['name'] for dev in self.output_devices if dev['index'] == self.selected_output_device)
                self.output_dropdown.set(current_name)
            except StopIteration:
                pass
        elif output_device_names and output_device_names[0] != "No output devices found":
            self.output_dropdown.set(output_device_names[0])
            
        # Test output button
        self.test_output_button = ctk.CTkButton(
            output_frame,
            text="🔊 Test",
            width=80,
            command=self._test_output_device,
            corner_radius=8,
            state="normal" if output_device_names[0] != "No output devices found" else "disabled"
        )
        self.test_output_button.grid(row=0, column=2, padx=(0, 15), pady=15)
        
        # Audio quality settings
        quality_frame = ctk.CTkFrame(main_frame, corner_radius=0)
        quality_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        quality_frame.grid_columnconfigure(1, weight=1)
        
        quality_label = ctk.CTkLabel(
            quality_frame,
            text="⚙️ Audio Quality:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        quality_label.grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        # Sample rate dropdown
        sample_rates = ["48000 Hz (Recommended)", "44100 Hz", "32000 Hz", "16000 Hz"]
        self.sample_rate_dropdown = ctk.CTkComboBox(
            quality_frame,
            values=sample_rates,
            state="readonly",
            width=200
        )
        self.sample_rate_dropdown.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="w")
        
        # Set current sample rate
        current_sample_rate = self.current_settings.get('sample_rate', 48000)
        for rate_option in sample_rates:
            if str(current_sample_rate) in rate_option:
                self.sample_rate_dropdown.set(rate_option)
                break
        else:
            self.sample_rate_dropdown.set(sample_rates[0])
            
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, corner_radius=0, fg_color="transparent")
        button_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 20))
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=120,
            corner_radius=8,
            height=40,
            command=self._cancel,
            fg_color=("gray60", "gray30"),
            hover_color=("gray50", "gray40")
        )
        cancel_button.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="e")
        
        save_button = ctk.CTkButton(
            button_frame,
            text="Save Settings",
            width=120,
            corner_radius=8,
            height=40,
            command=self._save_settings,
            font=ctk.CTkFont(weight="bold")
        )
        save_button.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="w")
        
    def _test_input_device(self):
        """Test the selected input device."""
        if not SOUNDDEVICE_AVAILABLE:
            messagebox.showwarning("Audio Testing", "Audio testing is not available because sounddevice is not installed.\n\nPlease install it with: pip install sounddevice")
            return
            
        try:
            selected_name = self.input_dropdown.get()
            device_index = next(dev['index'] for dev in self.input_devices if dev['name'] == selected_name)
            
            # Test recording for 2 seconds
            messagebox.showinfo("Testing Input", f"Testing input device: {selected_name}\n\nSpeak into your microphone for 2 seconds...")
            
            import numpy as np
            duration = 2  # seconds
            samplerate = 44100
            
            # Record audio
            recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, device=device_index)
            sd.wait()
            
            # Check if any audio was captured
            max_amplitude = np.max(np.abs(recording))
            if max_amplitude > 0.01:  # Threshold for detecting audio
                messagebox.showinfo("Test Result", f"✅ Input device working!\n\nDetected audio level: {max_amplitude:.3f}")
            else:
                messagebox.showwarning("Test Result", "⚠️ No audio detected.\n\nPlease check your microphone connection and try speaking louder.")
                
        except Exception as e:
            logger.error(f"Failed to test input device: {e}")
            messagebox.showerror("Test Failed", f"Failed to test input device:\n{e}")
            
    def _test_output_device(self):
        """Test the selected output device."""
        if not SOUNDDEVICE_AVAILABLE:
            messagebox.showwarning("Audio Testing", "Audio testing is not available because sounddevice is not installed.\n\nPlease install it with: pip install sounddevice")
            return
            
        try:
            selected_name = self.output_dropdown.get()
            device_index = next(dev['index'] for dev in self.output_devices if dev['name'] == selected_name)
            
            # Generate a test tone
            import numpy as np
            duration = 2  # seconds
            samplerate = 44100
            frequency = 440  # A4 note
            
            # Generate sine wave
            t = np.linspace(0, duration, int(samplerate * duration), False)
            test_tone = 0.1 * np.sin(2 * np.pi * frequency * t)
            
            messagebox.showinfo("Testing Output", f"Playing test tone on: {selected_name}\n\nYou should hear a 2-second tone.")
            
            # Play the test tone
            sd.play(test_tone, samplerate=samplerate, device=device_index)
            sd.wait()
            
            messagebox.showinfo("Test Complete", "✅ Test tone completed!\n\nDid you hear the sound?")
            
        except Exception as e:
            logger.error(f"Failed to test output device: {e}")
            messagebox.showerror("Test Failed", f"Failed to test output device:\n{e}")
            
    def _save_settings(self):
        """Save the audio settings."""
        try:
            settings = {}
            
            # Get selected input device
            if self.input_dropdown.get() != "No input devices found":
                selected_input_name = self.input_dropdown.get()
                input_device_index = next(dev['index'] for dev in self.input_devices if dev['name'] == selected_input_name)
                settings['input_device'] = input_device_index
                settings['input_device_name'] = selected_input_name
            
            # Get selected output device
            if self.output_dropdown.get() != "No output devices found":
                selected_output_name = self.output_dropdown.get()
                output_device_index = next(dev['index'] for dev in self.output_devices if dev['name'] == selected_output_name)
                settings['output_device'] = output_device_index
                settings['output_device_name'] = selected_output_name
            
            # Get sample rate
            sample_rate_text = self.sample_rate_dropdown.get()
            sample_rate = int(sample_rate_text.split()[0])
            settings['sample_rate'] = sample_rate
            
            # Call the callback if set
            if self.on_settings_saved:
                self.on_settings_saved(settings)
            
            logger.info(f"Audio settings saved: {settings}")
            self._close_dialog()
            
        except Exception as e:
            logger.error(f"Failed to save audio settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings:\n{e}")
            
    def _cancel(self):
        """Cancel and close the dialog."""
        self._close_dialog()
        
    def _close_dialog(self):
        """Close the dialog."""
        if self.dialog:
            try:
                self.dialog.grab_release()
            except Exception:
                # Ignore grab_release errors
                pass
            try:
                self.dialog.destroy()
            except Exception:
                # Ignore destroy errors
                pass
            self.dialog = None 
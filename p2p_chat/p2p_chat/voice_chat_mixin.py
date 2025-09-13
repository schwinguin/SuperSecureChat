"""
Voice Chat Mixin for P2P Chat Application.
Extends RTCPeer with voice communication capabilities using WebRTC audio tracks.
"""

import asyncio
import logging
import numpy as np
import sounddevice as sd
from typing import Optional, Callable
from aiortc import MediaStreamTrack, RTCPeerConnection
from aiortc.contrib.media import MediaRecorder, MediaPlayer
import av

logger = logging.getLogger(__name__)


class AudioInputTrack(MediaStreamTrack):
    """
    Audio track that captures audio from the microphone.
    Uses sounddevice for low-latency audio capture.
    """
    kind = "audio"
    
    def __init__(self, sample_rate=48000, channels=1, frames_per_buffer=1024, device=None):
        super().__init__()
        self.sample_rate = sample_rate
        self.channels = channels
        self.frames_per_buffer = frames_per_buffer
        self.audio_queue = asyncio.Queue(maxsize=10)
        self.running = False
        self.stream = None
        self.device = device
        
    def audio_callback(self, indata, frames, time, status):
        """Callback for sounddevice stream."""
        if status:
            logger.warning(f"Audio input status: {status}")
        
        # Convert to the format expected by aiortc
        audio_data = indata.copy()
        if not self.audio_queue.full():
            try:
                self.audio_queue.put_nowait(audio_data)
            except asyncio.QueueFull:
                pass  # Drop frame if queue is full
    
    async def start(self):
        """Start audio capture."""
        if self.running:
            return
            
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='float32',
                blocksize=self.frames_per_buffer,
                callback=self.audio_callback,
                latency='low',
                device=self.device
            )
            self.stream.start()
            self.running = True
            logger.info(f"Audio input started: {self.sample_rate}Hz, {self.channels} channels")
        except Exception as e:
            logger.error(f"Failed to start audio input: {e}")
            raise
    
    async def stop(self):
        """Stop audio capture."""
        if not self.running:
            return
            
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        logger.info("Audio input stopped")
    
    async def recv(self):
        """Receive audio frame."""
        if not self.running:
            # Return silence if not recording
            silence = np.zeros((self.frames_per_buffer, self.channels), dtype=np.float32)
            frame = av.AudioFrame.from_ndarray(silence, format='flt', layout='mono' if self.channels == 1 else 'stereo')
            frame.sample_rate = self.sample_rate
            frame.pts = 0
            frame.time_base = av.Rational(1, self.sample_rate)
            return frame
        
        try:
            # Wait for audio data with timeout
            audio_data = await asyncio.wait_for(self.audio_queue.get(), timeout=0.1)
            
            # Create AudioFrame from numpy array
            frame = av.AudioFrame.from_ndarray(audio_data, format='flt', layout='mono' if self.channels == 1 else 'stereo')
            frame.sample_rate = self.sample_rate
            frame.pts = 0
            frame.time_base = av.Rational(1, self.sample_rate)
            
            return frame
            
        except asyncio.TimeoutError:
            # Return silence if no data available
            silence = np.zeros((self.frames_per_buffer, self.channels), dtype=np.float32)
            frame = av.AudioFrame.from_ndarray(silence, format='flt', layout='mono' if self.channels == 1 else 'stereo')
            frame.sample_rate = self.sample_rate
            frame.pts = 0
            frame.time_base = av.Rational(1, self.sample_rate)
            return frame


class AudioOutputHandler:
    """
    Handles audio output/playback using sounddevice.
    Receives audio frames from WebRTC and plays them through speakers.
    """
    
    def __init__(self, sample_rate=48000, channels=1, frames_per_buffer=1024, device=None):
        self.sample_rate = sample_rate
        self.channels = channels
        self.frames_per_buffer = frames_per_buffer
        self.audio_queue = asyncio.Queue(maxsize=20)
        self.running = False
        self.stream = None
        self.playback_task = None
        self.device = device
        
    def audio_callback(self, outdata, frames, time, status):
        """Callback for sounddevice output stream."""
        if status:
            logger.warning(f"Audio output status: {status}")
        
        try:
            # Get audio data from queue (non-blocking)
            if not self.audio_queue.empty():
                audio_data = self.audio_queue.get_nowait()
                if audio_data.shape[0] >= frames:
                    outdata[:] = audio_data[:frames]
                else:
                    # Pad with zeros if not enough data
                    outdata[:audio_data.shape[0]] = audio_data
                    outdata[audio_data.shape[0]:] = 0
            else:
                # No data available, output silence
                outdata.fill(0)
        except Exception as e:
            logger.error(f"Error in audio output callback: {e}")
            outdata.fill(0)
    
    async def start(self):
        """Start audio playback."""
        if self.running:
            return
            
        try:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='float32',
                blocksize=self.frames_per_buffer,
                callback=self.audio_callback,
                latency='low',
                device=self.device
            )
            self.stream.start()
            self.running = True
            logger.info(f"Audio output started: {self.sample_rate}Hz, {self.channels} channels")
        except Exception as e:
            logger.error(f"Failed to start audio output: {e}")
            raise
    
    async def stop(self):
        """Stop audio playback."""
        if not self.running:
            return
            
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        logger.info("Audio output stopped")
    
    async def play_frame(self, frame):
        """Queue an audio frame for playback."""
        if not self.running:
            return
            
        try:
            # Convert AudioFrame to numpy array
            audio_data = frame.to_ndarray()
            
            # Ensure correct shape (samples, channels)
            if audio_data.ndim == 1:
                audio_data = audio_data.reshape(-1, 1)
            elif audio_data.ndim == 2 and audio_data.shape[0] < audio_data.shape[1]:
                audio_data = audio_data.T
            
            # Queue for playback (drop if queue is full)
            if not self.audio_queue.full():
                await self.audio_queue.put(audio_data)
        except Exception as e:
            logger.error(f"Error queuing audio frame: {e}")


class VoiceChatMixin:
    """
    Mixin to add voice chat capabilities to RTCPeer.
    Provides methods to start/stop voice chat while maintaining text chat functionality.
    """
    
    def __init__(self):
        # Voice chat components
        self.audio_input_track: Optional[AudioInputTrack] = None
        self.audio_output_handler: Optional[AudioOutputHandler] = None
        self.voice_enabled = False
        self.voice_transmitting = False
        self.remote_audio_track = None
        
        # Voice chat callbacks
        self.on_voice_state_change: Optional[Callable] = None
        
        # Audio settings (will be set from application settings)
        self.audio_sample_rate = 48000
        self.audio_channels = 1
        self.audio_frames_per_buffer = 1024
        self.audio_input_device = None
        self.audio_output_device = None
        
        # Initialize audio components
        self._init_voice_components()
    
    def _init_voice_components(self):
        """Initialize voice chat components."""
        self.audio_input_track = AudioInputTrack(
            sample_rate=self.audio_sample_rate,
            channels=self.audio_channels,
            frames_per_buffer=self.audio_frames_per_buffer,
            device=self.audio_input_device
        )
        
        self.audio_output_handler = AudioOutputHandler(
            sample_rate=self.audio_sample_rate,
            channels=self.audio_channels,
            frames_per_buffer=self.audio_frames_per_buffer,
            device=self.audio_output_device
        )
    
    def update_audio_settings(self, settings: dict):
        """Update audio settings and reinitialize components if needed."""
        # Update settings
        self.audio_sample_rate = settings.get('sample_rate', 48000)
        self.audio_channels = settings.get('channels', 1)
        self.audio_frames_per_buffer = settings.get('frames_per_buffer', 1024)
        self.audio_input_device = settings.get('input_device', None)
        self.audio_output_device = settings.get('output_device', None)
        
        # If voice chat is currently enabled, we need to restart it with new settings
        was_enabled = self.voice_enabled
        was_transmitting = self.voice_transmitting
        
        if was_enabled:
            # Disable temporarily
            asyncio.create_task(self.disable_voice_chat())
            
        # Reinitialize components
        self._init_voice_components()
        
        if was_enabled:
            # Re-enable with new settings
            asyncio.create_task(self._restart_voice_chat(was_transmitting))
            
        logger.info(f"Audio settings updated: input_device={self.audio_input_device}, output_device={self.audio_output_device}, sample_rate={self.audio_sample_rate}")
    
    async def _restart_voice_chat(self, was_transmitting: bool):
        """Restart voice chat after settings change."""
        try:
            await asyncio.sleep(0.1)  # Small delay to ensure cleanup is complete
            await self.enable_voice_chat()
            
            if was_transmitting:
                await self.start_voice_transmission()
                
        except Exception as e:
            logger.error(f"Failed to restart voice chat: {e}")
    
    async def enable_voice_chat(self):
        """Enable voice chat functionality."""
        if self.voice_enabled:
            return
        
        try:
            # Start audio output handler
            await self.audio_output_handler.start()
            
            # Add audio input track to peer connection if connected
            if self.pc and self.pc.connectionState == "connected":
                await self._add_audio_track()
            
            self.voice_enabled = True
            logger.info("Voice chat enabled")
            
            # Send voice status update to peer
            if hasattr(self, 'send_voice_status_update'):
                self.send_voice_status_update(True, self.local_username)
            
            if self.on_voice_state_change:
                await self.on_voice_state_change("enabled")
                
        except Exception as e:
            logger.error(f"Failed to enable voice chat: {e}")
            if self.on_voice_state_change:
                await self.on_voice_state_change("error", str(e))
    
    async def disable_voice_chat(self):
        """Disable voice chat functionality."""
        if not self.voice_enabled:
            return
        
        try:
            # Stop transmission
            await self.stop_voice_transmission()
            
            # Stop audio components
            if self.audio_input_track:
                await self.audio_input_track.stop()
            
            if self.audio_output_handler:
                await self.audio_output_handler.stop()
            
            self.voice_enabled = False
            logger.info("Voice chat disabled")
            
            # Send voice status update to peer
            if hasattr(self, 'send_voice_status_update'):
                self.send_voice_status_update(False, self.local_username)
            
            if self.on_voice_state_change:
                await self.on_voice_state_change("disabled")
                
        except Exception as e:
            logger.error(f"Failed to disable voice chat: {e}")
    
    async def start_voice_transmission(self):
        """Start transmitting voice (push-to-talk or toggle)."""
        if not self.voice_enabled or self.voice_transmitting:
            return
        
        try:
            # Start audio input
            await self.audio_input_track.start()
            self.voice_transmitting = True
            logger.info("Voice transmission started")
            
            if self.on_voice_state_change:
                await self.on_voice_state_change("transmitting")
                
        except Exception as e:
            logger.error(f"Failed to start voice transmission: {e}")
    
    async def stop_voice_transmission(self):
        """Stop transmitting voice."""
        if not self.voice_transmitting:
            return
        
        try:
            # Stop audio input
            if self.audio_input_track:
                await self.audio_input_track.stop()
            
            self.voice_transmitting = False
            logger.info("Voice transmission stopped")
            
            if self.on_voice_state_change:
                await self.on_voice_state_change("listening")
                
        except Exception as e:
            logger.error(f"Failed to stop voice transmission: {e}")
    
    async def _add_audio_track(self):
        """Add audio track to peer connection."""
        if not self.pc or not self.audio_input_track:
            return
        
        try:
            # Check if audio track is already added
            for sender in self.pc.getSenders():
                if sender.track and sender.track.kind == "audio":
                    logger.info("Audio track already added")
                    return
            
            # Add the audio track
            self.pc.addTrack(self.audio_input_track)
            logger.info("Audio track added to peer connection")
            
        except Exception as e:
            logger.error(f"Failed to add audio track: {e}")
    
    def _setup_audio_track_handler(self, track):
        """Set up handler for incoming audio track."""
        logger.info(f"Setting up audio track handler for {track.kind} track")
        
        if track.kind == "audio":
            self.remote_audio_track = track
            
            # Start task to handle incoming audio
            asyncio.create_task(self._handle_incoming_audio(track))
    
    async def _handle_incoming_audio(self, track):
        """Handle incoming audio frames from remote peer."""
        logger.info("Started handling incoming audio")
        
        try:
            while True:
                try:
                    frame = await track.recv()
                    
                    # Play the received audio
                    if self.audio_output_handler and self.voice_enabled:
                        await self.audio_output_handler.play_frame(frame)
                        
                except Exception as e:
                    if "ended" in str(e).lower():
                        break
                    logger.error(f"Error receiving audio frame: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in audio handling: {e}")
        finally:
            logger.info("Stopped handling incoming audio")
    
    def is_voice_enabled(self) -> bool:
        """Check if voice chat is enabled."""
        return self.voice_enabled
    
    def is_voice_transmitting(self) -> bool:
        """Check if currently transmitting voice."""
        return self.voice_transmitting
    
    async def _cleanup_voice_chat(self):
        """Clean up voice chat resources."""
        try:
            await self.disable_voice_chat()
        except Exception as e:
            logger.error(f"Error cleaning up voice chat: {e}") 
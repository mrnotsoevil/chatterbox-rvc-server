"""
Audio playback functionality
"""

import asyncio
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Union
from .exceptions import AudioError


class AudioPlayer:
    """Audio playback functionality"""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.temp_dir = tempfile.gettempdir()
    
    async def play_audio(self, audio_path: str, volume: float = 1.0):
        """Play audio file"""
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            if self.platform == "linux":
                await self._play_linux(audio_path, volume)
            elif self.platform == "darwin":  # macOS
                await self._play_macos(audio_path, volume)
            elif self.platform == "windows":
                await self._play_windows(audio_path, volume)
            else:
                raise AudioError(f"Unsupported platform: {self.platform}")
                
        except Exception as e:
            raise AudioError(f"Failed to play audio: {e}")
    
    async def _play_linux(self, audio_path: str, volume: float):
        """Play audio on Linux using aplay or paplay"""
        try:
            # Try aplay first
            subprocess.run(['aplay', audio_path], check=True, timeout=10)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            try:
                # Fallback to paplay
                subprocess.run(['paplay', audio_path], check=True, timeout=10)
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                # Fallback to python sound playback if available
                await self._play_python_fallback(audio_path)
    
    async def _play_macos(self, audio_path: str, volume: float):
        """Play audio on macOS using afplay"""
        try:
            # Use afplay with volume control if possible
            subprocess.run(['afplay', audio_path], check=True, timeout=10)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            await self._play_python_fallback(audio_path)
    
    async def _play_windows(self, audio_path: str, volume: float):
        """Play audio on Windows using PowerShell"""
        try:
            # Use PowerShell to play audio with better error handling
            ps_command = f"""
            Add-Type -TypeDefinition @"
            using System;
            using System.Runtime.InteropServices;
            public class Audio {{
                [DllImport("winmm.dll")]
                public static extern int mciSendString(string command, StringBuilder buffer, int bufferSize, IntPtr hwnd);
            }}
"@;
            $audio = New-Object Audio;
            $audio.mciSendString("open \"{audio_path}\" type mpegvideo alias media", $null, 0, $null);
            $audio.mciSendString("play media wait", $null, 0, $null);
            $audio.mciSendString("close media", $null, 0, $null);
            """
            
            process = subprocess.Popen(
                ['powershell', '-Command', ps_command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            process.communicate(timeout=30)  # Increased timeout for longer audio
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            await self._play_python_fallback(audio_path)
    
    async def _play_python_fallback(self, audio_path: str):
        """Fallback audio playback using Python"""
        try:
            # Try to use pygame if available
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            
            pygame.mixer.quit()
        except ImportError:
            try:
                # Try to use simpleaudio if pygame is not available
                import simpleaudio
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                wave_obj = simpleaudio.WaveObject.from_wave_file(audio_path)
                play_obj = wave_obj.play()
                play_obj.wait_done()
            except ImportError:
                raise AudioError("No audio playback method available. Please install audio dependencies (pygame or simpleaudio).")
            except Exception as e:
                raise AudioError(f"SimpleAudio fallback playback failed: {e}")
        except Exception as e:
            raise AudioError(f"Python fallback playback failed: {e}")
    
    async def play(self, audio_data: Union[str, bytes], volume: float = 1.0):
        """Play audio from file path or bytes data
        
        Args:
            audio_data: Either file path (str) or audio data (bytes)
            volume: Volume level (0.0 to 1.0)
        """
        if isinstance(audio_data, str):
            # It's a file path
            await self.play_audio(audio_data, volume)
        elif isinstance(audio_data, bytes):
            # It's audio data, save to temp file and play
            await self._play_from_bytes(audio_data, volume)
        else:
            raise AudioError(f"Invalid audio data type: {type(audio_data)}")
    
    async def _play_from_bytes(self, audio_data: bytes, volume: float):
        """Play audio from bytes data by saving to temp file"""
        try:
            # Create a temporary file
            temp_file = Path(self.temp_dir) / f"audio_{hash(audio_data)}.wav"
            
            # Write audio data to temp file
            with open(temp_file, 'wb') as f:
                f.write(audio_data)
            
            # Play the temp file
            await self.play_audio(str(temp_file), volume)
            
            # Clean up temp file
            try:
                temp_file.unlink()
            except OSError:
                pass  # Ignore cleanup errors
                
        except Exception as e:
            raise AudioError(f"Failed to play audio from bytes: {e}")
    
    def get_supported_formats(self) -> list:
        """Get list of supported audio formats"""
        return ['wav', 'flac', 'ogg', 'mp3', 'm4a', 'aac']
    
    def is_format_supported(self, format_name: str) -> bool:
        """Check if format is supported"""
        return format_name.lower() in self.get_supported_formats()
    
    def get_platform_info(self) -> dict:
        """Get platform-specific audio information"""
        return {
            "platform": self.platform,
            "supported_formats": self.get_supported_formats(),
            "available_methods": self._get_available_methods()
        }
    
    def _get_available_methods(self) -> list:
        """Get list of available audio playback methods"""
        methods = []
        
        # Check system methods
        if self.platform == "linux":
            if self._command_exists("aplay"):
                methods.append("aplay")
            if self._command_exists("paplay"):
                methods.append("paplay")
        elif self.platform == "darwin":
            if self._command_exists("afplay"):
                methods.append("afplay")
        elif self.platform == "windows":
            methods.append("powershell")
        
        # Check Python methods
        try:
            import pygame
            methods.append("pygame")
        except ImportError:
            pass
        
        try:
            import simpleaudio
            methods.append("simpleaudio")
        except ImportError:
            pass
        
        return methods
    
    def _command_exists(self, command: str) -> bool:
        """Check if a command exists on the system"""
        try:
            subprocess.run(['which', command], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
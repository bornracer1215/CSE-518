"""
Text-to-Speech Engine for Gesture-Based Adaptive Reading Interface
Uses edge-tts (Microsoft Edge voices) with pygame for playback
"""

import asyncio
import edge_tts
import pygame
import tempfile
import os
import threading
import time
import config


class TTSEngine:
    def __init__(self, root=None, on_word_callback=None, on_complete_callback=None):
        """
        Initialize the TTS engine
        """
        self.root = root
        self.on_complete_callback = on_complete_callback
        
        # State management
        self.is_speaking = False
        self.is_paused = False
        self.should_stop = False
        
        # Settings
        self.current_rate = config.TTS_DEFAULT_RATE
        self.current_voice = "en-US-AriaNeural"
        
        # Available voices
        self.available_voices = [
            ("en-US-AriaNeural", "Aria (US Female)"),
            ("en-US-GuyNeural", "Guy (US Male)"),
            ("en-US-JennyNeural", "Jenny (US Female)"),
            ("en-GB-SoniaNeural", "Sonia (UK Female)"),
            ("en-GB-RyanNeural", "Ryan (UK Male)"),
            ("en-AU-NatashaNeural", "Natasha (AU Female)"),
        ]
        
        # Temp file for audio
        self.temp_dir = tempfile.mkdtemp()
        self.audio_file = os.path.join(self.temp_dir, "speech.mp3")
        
        # Thread for async operations
        self.speech_thread = None
        
        # Initialize pygame mixer
        self._init_pygame()
    
    def _init_pygame(self):
        """Initialize or reinitialize pygame mixer"""
        try:
            pygame.mixer.quit()
        except:
            pass
        pygame.mixer.init()
    
    def get_available_voices(self):
        """Return list of available voice names"""
        return [(i, name) for i, (voice_id, name) in enumerate(self.available_voices)]
    
    def set_voice(self, voice_index):
        """Set the voice by index"""
        if 0 <= voice_index < len(self.available_voices):
            self.current_voice = self.available_voices[voice_index][0]
    
    def get_rate(self):
        """Get current speech rate"""
        return self.current_rate
    
    def set_rate(self, rate):
        """Set speech rate"""
        rate = max(config.TTS_MIN_RATE, min(config.TTS_MAX_RATE, rate))
        self.current_rate = rate
    
    def _rate_to_percent(self):
        """Convert rate (WPM) to edge-tts percentage format"""
        percent = ((self.current_rate - 150) / 150) * 100
        percent = max(-50, min(100, percent))
        if percent >= 0:
            return f"+{int(percent)}%"
        else:
            return f"{int(percent)}%"
    
    async def _generate_speech(self, text):
        """Generate speech audio file"""
        rate_str = self._rate_to_percent()
        communicate = edge_tts.Communicate(text, self.current_voice, rate=rate_str)
        await communicate.save(self.audio_file)
    
    def _speak_thread_func(self, text):
        """Thread function to generate and play speech"""
        try:
            # Reinitialize pygame for fresh start
            self._init_pygame()
            
            # Generate audio file
            asyncio.run(self._generate_speech(text))
            
            if self.should_stop:
                self.is_speaking = False
                return
            
            # Load and play audio
            pygame.mixer.music.load(self.audio_file)
            pygame.mixer.music.play()
            
            is_paused_locally = False
            
            while True:
                # Check for stop
                if self.should_stop:
                    pygame.mixer.music.stop()
                    break
                
                # Handle pause state changes
                if self.is_paused and not is_paused_locally:
                    pygame.mixer.music.pause()
                    is_paused_locally = True
                elif not self.is_paused and is_paused_locally:
                    pygame.mixer.music.unpause()
                    is_paused_locally = False
                
                # If paused, just wait
                if is_paused_locally:
                    time.sleep(0.05)
                    continue
                
                # Check if music is still playing
                if not pygame.mixer.music.get_busy():
                    break
                
                time.sleep(0.05)
            
            # Finished
            self.is_speaking = False
            
            # Only callback if not stopped and root still exists
            if self.on_complete_callback and self.root and not self.should_stop:
                try:
                    self.root.after(0, self.on_complete_callback)
                except:
                    pass  # Window was closed, ignore
                
        except Exception as e:
            print(f"TTS Error: {e}")
            self.is_speaking = False
    
    def speak(self, text, start_from_index=0):
        """Start speaking the given text"""
        # Full stop and reset
        self.stop()
        time.sleep(0.1)
        
        # Trim text if starting from middle
        if start_from_index > 0:
            text = text[start_from_index:]
        
        if not text.strip():
            print("No text to speak")
            return
        
        self.should_stop = False
        self.is_paused = False
        self.is_speaking = True
        
        # Start speech in background thread
        self.speech_thread = threading.Thread(target=self._speak_thread_func, args=(text,), daemon=True)
        self.speech_thread.start()
    
    def pause(self):
        """Pause speech"""
        if self.is_speaking and not self.is_paused:
            self.is_paused = True
            return True
        return False
    
    def resume(self):
        """Resume paused speech"""
        if self.is_speaking and self.is_paused:
            self.is_paused = False
            return True
        return False
    
    def toggle_pause(self):
        """Toggle between pause and resume"""
        if self.is_paused:
            return self.resume()
        else:
            return self.pause()
    
    def stop(self):
        """Stop speech completely"""
        self.should_stop = True
        self.is_paused = False
        
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except:
            pass
        
        # Wait for thread to finish
        if self.speech_thread and self.speech_thread.is_alive():
            self.speech_thread.join(timeout=1.0)
        
        self.is_speaking = False
    
    def get_state(self):
        """Get current state as string"""
        if not self.is_speaking:
            return "stopped"
        elif self.is_paused:
            return "paused"
        else:
            return "playing"
    
    def cleanup(self):
        """Clean up resources"""
        self.stop()
        try:
            pygame.mixer.quit()
            if os.path.exists(self.audio_file):
                os.remove(self.audio_file)
            os.rmdir(self.temp_dir)
        except:
            pass


# Test
if __name__ == "__main__":
    print("Testing edge-tts engine...")
    
    def on_complete():
        print("--- Done ---")
    
    tts = TTSEngine(root=None, on_complete_callback=on_complete)
    
    print("\nAvailable voices:")
    for i, name in tts.get_available_voices():
        print(f"  {i}: {name}")
    
    print("\nSpeaking test sentence...")
    
    async def test():
        communicate = edge_tts.Communicate("Hello, this is a test.", "en-US-AriaNeural")
        await communicate.save("test_audio.mp3")
        
        pygame.mixer.init()
        pygame.mixer.music.load("test_audio.mp3")
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        os.remove("test_audio.mp3")
        print("Done!")
    
    asyncio.run(test())
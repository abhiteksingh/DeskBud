import speech_recognition as sr
from PyQt5.QtCore import QThread, pyqtSignal

class AetherVoiceListener(QThread):
    # Signals to communicate with the main coordinator
    wake_word_detected = pyqtSignal()
    command_transcribed = pyqtSignal(str)
    status_changed = pyqtSignal(str)  # Sends status descriptions

    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()
        # Set energy threshold, dynamic energy settings, and pause limits for single-sentence flow
        self.recognizer.energy_threshold = 150
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.pause_threshold = 1.3  # Wait longer before slicing phrase to capture pause between wake word & command
        self.recognizer.non_speaking_duration = 0.5
        self.running = True
        self.listening_for_command = False
        self.microphone = None
        
        # Test microphone access
        try:
            self.microphone = sr.Microphone()
        except Exception as e:
            print(f"Error accessing microphone: {str(e)}")

    def run(self):
        if not self.microphone:
            self.status_changed.emit("Mic Unavailable")
            return

        with self.microphone as source:
            # Calibrate recognizer for ambient noise
            self.status_changed.emit("Calibrating mic...")
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.8)
                # Cap calibrated threshold to keep mic highly sensitive
                if self.recognizer.energy_threshold > 200:
                    self.recognizer.energy_threshold = 200
                elif self.recognizer.energy_threshold < 50:
                    self.recognizer.energy_threshold = 50
            except Exception as e:
                print(f"Failed to adjust for ambient noise: {e}")
                
            self.status_changed.emit("Idle")

            while self.running:
                try:
                    # Listen for audio block
                    self.status_changed.emit("Listening (passive)...")
                    # Increased limit from 4 to 8 seconds to give user time to speak their full command
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=8)
                    
                    if not self.running:
                        break
                        
                    # Attempt transcription
                    try:
                        text = self.recognizer.recognize_google(audio).lower().strip()
                        print(f"Voice Heard: '{text}'")
                        
                        if self.listening_for_command:
                            # We were actively waiting for a command after a previous wake word
                            self.command_transcribed.emit(text)
                            self.listening_for_command = False
                        else:
                            # We are looking for the wake word
                            # Support variations and phonetic misinterpretations of "Aether"
                            wake_triggers = ["wake up", "wake"]
                            matched_trigger = None
                            for trigger in wake_triggers:
                                if trigger in text:
                                    matched_trigger = trigger
                                    break
                            
                            if matched_trigger:
                                self.wake_word_detected.emit()
                                
                                # Check if there is an inline command in the same audio block
                                # e.g. "hey aether open google chrome"
                                parts = text.split(matched_trigger, 1)
                                if len(parts) > 1 and parts[1].strip():
                                    inline_cmd = parts[1].strip()
                                    self.command_transcribed.emit(inline_cmd)
                                else:
                                    # Just said the wake word, set flag to capture the next block as the command
                                    self.listening_for_command = True
                                    self.status_changed.emit("Listening (active)...")
                                    
                    except sr.UnknownValueError:
                        # Speech was unintelligible, just continue
                        continue
                    except sr.RequestError as e:
                        print(f"Could not request results from Google Speech Recognition service; {e}")
                        self.status_changed.emit("Speech service error")
                        QThread.msleep(5000)
                        
                except Exception as e:
                    print(f"Error in speech loop: {str(e)}")
                    QThread.msleep(2000)

    def stop(self):
        self.running = False
        self.terminate()
        self.wait()

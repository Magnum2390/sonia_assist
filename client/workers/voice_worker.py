from PyQt6.QtCore import QThread, pyqtSignal
import speech_recognition as sr

class VoiceWorker(QThread):
    voice_detected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.recognizer = sr.Recognizer()
        # Configuration Audio (Optimized for Long Sentences & Reactivity)
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.6  # Sweet spot (0.8 was too slow, 0.4 too fast)
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.3 # Reduced slighly for reactivity
    
    def run(self):
        with sr.Microphone() as source:
            print("🎤 Microphone initialized")
            while self.running:
                try:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    # Whisper local ou Google
                    text = self.recognizer.recognize_google(audio, language="en-US")
                    if text:
                        self.voice_detected.emit(text)
                except:
                    pass
    
    def stop(self):
        self.running = False

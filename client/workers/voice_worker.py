from PyQt6.QtCore import QThread, pyqtSignal
import speech_recognition as sr

class VoiceWorker(QThread):
    voice_detected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.recognizer = sr.Recognizer()
        # Configuration Audio (Ultra-Fast / Aggressive)
        self.recognizer.energy_threshold = 280 # Slightly more sensitive
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.4 # 0.2s is too risky (cuts words), 0.4s is the "Alexa" sweet spot
        self.recognizer.phrase_threshold = 0.2
        self.recognizer.non_speaking_duration = 0.2 # Instant cut after silence
    
    def run(self):
        with sr.Microphone() as source:
            print("🎤 Microphone initialized")
            while self.running:
                try:
                    # print("DEBUG: Listening...")
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    # Whisper local ou Google
                    import time
                    start_stt = time.time()
                    text = self.recognizer.recognize_google(audio, language="en-US")
                    end_stt = time.time()
                    if text:
                        print(f"⏱️ STT Duration: {end_stt - start_stt:.2f}s | Text: {text}")
                        self.voice_detected.emit(text)
                except:
                    pass
    
    def stop(self):
        self.running = False

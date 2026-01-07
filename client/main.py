
import sys
import os
import requests
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
# Ugly import fix relative path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from streaming_tts import StreamingTTS, StreamingAI
from optimized_hud import OptimizedHUD
import speech_recognition as sr

# Configuration
SERVER_URL = "http://localhost:8000"

# --- Workers ---

class VoiceWorker(QThread):
    voice_detected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.pause_threshold = 0.6
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.4
        self.recognizer.dynamic_energy_threshold = False
    
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

class APIWorker(QThread):
    token_received = pyqtSignal(str)
    response_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.query = None
        self.endpoint = "/chat" # /chat or /execute
    
    def set_query(self, query, endpoint="/chat"):
        self.query = query
        self.endpoint = endpoint
        
    def run(self):
        if not self.query: return
        
        try:
            if self.endpoint == "/chat":
                # Streaming Response
                full_resp = ""
                with requests.post(f"{SERVER_URL}/chat", json={"query": self.query}, stream=True) as r:
                    if r.status_code == 200:
                        for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
                            if chunk:
                                self.token_received.emit(chunk)
                                full_resp += chunk
                        self.response_complete.emit(full_resp)
                    else:
                        self.error_occurred.emit(f"Server Error: {r.status_code}")
            
            elif self.endpoint == "/execute":
                 # Execution (Blocking)
                 r = requests.post(f"{SERVER_URL}/execute", json={"command": self.query})
                 if r.status_code == 200:
                     data = r.json()
                     self.response_complete.emit(data.get("summary", "Done"))
                 else:
                     self.error_occurred.emit(f"Exec Error: {r.status_code}")
                     
        except Exception as e:
            self.error_occurred.emit(str(e))

# --- Main Client App ---

class SoniaClient:
    def __init__(self):
        print("🤖 Initializing Sonia Client...")
        self.app = QApplication(sys.argv)
        
        self.hud = OptimizedHUD("hud_icon.png") # Local path now
        self.tts = StreamingTTS()
        self.streaming_ai = StreamingAI(self.tts)
        
        self.voice_worker = VoiceWorker()
        self.api_worker = APIWorker()
        
        # Connections
        self.voice_worker.voice_detected.connect(self.on_voice_input)
        
        self.api_worker.token_received.connect(self.streaming_ai.process_token)
        self.api_worker.response_complete.connect(self.on_api_complete)
        self.api_worker.error_occurred.connect(self.on_error)
        
        self.wake_words = ["sonia", "sonya"]
        self.is_processing = False
        
    def start(self):
        self.hud.show()
        self.voice_worker.start()
        self.tts.speak_immediate("Client Connected. I'm ready.")
        sys.exit(self.app.exec())
        
    def on_voice_input(self, text):
        print(f"👂 Heard: {text}")
        
        # Wake Word Logic
        text_lower = text.lower()
        if not any(w in text_lower for w in self.wake_words) and not self.is_processing: return
        
        clean = text
        for w in self.wake_words:
            if w in text_lower:
                clean = re.split(w, text, flags=re.IGNORECASE)[-1].strip()
        
        if not clean:
            self.tts.speak_immediate("Yes?")
            return
            
        self.process_command(clean)
        
    def process_command(self, text):
        if self.is_processing: return
        self.is_processing = True
        self.hud.set_state("thinking")
        self.streaming_ai.reset()
        
        # Routing Logic (Client Side Routing ? Or Server Side ?)
        # Let's keep it simple: Client decides endpoint
        action_keywords = ["open", "run", "make", "delete", "close"]
        is_action = any(k in text.lower() for k in action_keywords)
        
        if is_action:
            print("Running Action...")
            self.tts.speak_immediate("On it.")
            self.api_worker.set_query(text, endpoint="/execute")
        else:
            print("Chatting...")
            self.api_worker.set_query(text, endpoint="/chat")
            
        self.api_worker.start()
        
    def on_api_complete(self, response):
        print("✅ Response Complete")
        self.streaming_ai.flush_buffer()
        
        if response and not self.streaming_ai.has_spoken:
            self.tts.speak_immediate(response)
            
        self.hud.set_state("speaking")
        QTimer.singleShot(2000, self.reset_state)
        
    def on_error(self, err):
        print(f"Server Error: {err}")
        self.tts.speak_immediate("I lost connection to my brain.")
        self.reset_state()
        
    def reset_state(self):
        self.is_processing = False
        self.hud.set_state("idle")

import re

if __name__ == "__main__":
    client = SoniaClient()
    client.start()

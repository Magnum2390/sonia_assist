
import sys
import os
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
# Local imports (Now legit!)
from streaming_tts import StreamingTTS, StreamingAI
from optimized_hud import OptimizedHUD
import datetime

# Configuration
SERVER_URL = "http://localhost:8000"

# --- Workers Imports ---
from workers.voice_worker import VoiceWorker
from workers.api_worker import APIWorker

# --- Main Client App ---

# --- Main Client App ---

class SoniaClient:
    def __init__(self):
        print("Initializing Sonia Client...")
        self.app = QApplication(sys.argv)
        
        # Robust Resource Loading
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, "hud_icon.png")
        
        self.hud = OptimizedHUD(icon_path) # Local path now
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
        
        # --- Conversation Mode (Jarvis Style) ---
        self.conversation_active = False
        self.conversation_timer = QTimer()
        self.conversation_timer.setSingleShot(True)
        self.conversation_timer.timeout.connect(self.end_conversation_mode)
        
    def end_conversation_mode(self):
        """Called when 20s have passed without voice"""
        if self.conversation_active:
            print("Conversation Timeout. Returning to sleep.")
            self.conversation_active = False
            self.hud.set_state("idle")
            # Optional: Play a "Sleep" sound
            # self.tts.speak_immediate("Sleeping.")
        
    def start(self):
        self.hud.show()
        self.voice_worker.start()
        
        # Dynamic Greeting
        hour = datetime.datetime.now().hour
        greeting = "Good Morning"
        if 12 <= hour < 18:
            greeting = "Good Afternoon"
        elif hour >= 18:
            greeting = "Good Evening"
            
        final_msg = f"{greeting}, Sir. All systems are fully operational. Awaiting your command."
        self.tts.speak_immediate(final_msg)
        
        # Activate Conversation Mode immediately
        print("Startup Complete -> Enter Conversation Mode")
        self.conversation_active = True
        self.hud.set_state("listening_active")
        self.conversation_timer.start(20000) # 20 seconds
        
        sys.exit(self.app.exec())
        
    def on_voice_input(self, text):
        # 1. Active Listening Mode (Jarvis Style)
        if self.conversation_active:
            # If we are already active, we process EVERYTHING.
            # And reset the timer.
            self.conversation_timer.start(20000) # 20 seconds
            self.process_command(text)
            return

        # 2. Wake Word Logic (Passive Mode)
        text_lower = text.lower()
        if not any(w in text_lower for w in self.wake_words) and not self.is_processing: return
        
        clean = text
        for w in self.wake_words:
            if w in text_lower:
                clean = re.split(w, text, flags=re.IGNORECASE)[-1].strip()
        
        # Activate Conversation Mode
        self.conversation_active = True
        self.hud.set_state("listening_active")
        self.conversation_timer.start(20000) # 20 seconds
        
        if not clean:
            # Silent wake (Visual feedback only via HUD)
            # self.tts.speak_immediate("Yes?")
            return
            
        self.process_command(clean)
        
    def process_command(self, text):
        if self.is_processing: return
        self.is_processing = True
        
        # STOP Timer during processing/speaking so it doesn't expire while she talks
        if self.conversation_active:
            self.conversation_timer.stop()
            
        self.hud.set_state("thinking")
        self.streaming_ai.reset()
        
        # Routing Logic
        # Let's keep it simple: Client decides endpoint
        action_keywords = ["open", "run", "make", "delete", "close"]
        is_action = any(k in text.lower() for k in action_keywords)
        
        if is_action:
            self.tts.speak_immediate("On it.")
            self.api_worker.set_query(text, endpoint="/execute")
        else:
            self.api_worker.set_query(text, endpoint="/chat")
            
        self.api_worker.start()
        
    def on_api_complete(self, response):
        print("Response Complete")
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
        if self.conversation_active:
            print("Action Complete. Resetting Conversation Timer (20s).")
            self.conversation_timer.start(20000) # Reset full 20s AFTER speaking
            self.hud.set_state("listening_active")
        else:
            self.hud.set_state("idle")

import re

if __name__ == "__main__":
    client = SoniaClient()
    client.start()

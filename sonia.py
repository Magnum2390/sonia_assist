#!/usr/bin/env python3
"""BOB 2.0 - The Unified Agent"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from loguru import logger

# Importation des modules optimisés existants
from streaming_tts import StreamingTTS, StreamingAI
from optimized_ollama import OptimizedOllama, SmartModelSelector
from optimized_hud import OptimizedHUD
from smart_cache import SmartCache

# Importation des nouveaux workers
from workers.execution import ExecutionWorker
from workers.sentinel import SentinelWorker
from workers.telegram_bot import TelegramWorker

# Importation pour la voix (réutilisation de optimized_bob logic mais inline ou import)
# Je vais réintégrer VoiceWorker ici pour simplifier les imports
import speech_recognition as sr

class VoiceWorker(QThread):
    """Thread d'écoute vocale"""
    voice_detected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.pause_threshold = 0.6 # Un peu plus relax que 0.5
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.4
        self.recognizer.dynamic_energy_threshold = False # Évite que le seuil grimpe trop haut avec le bruit
    
    def run(self):
        with sr.Microphone() as source:
            logger.info("🎤 Microphone initialized")
            while self.running:
                try:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    # Note: On pourrait utiliser Whisper local ici pour plus de rapidité/privacy
                    text = self.recognizer.recognize_google(audio, language="en-US")
                    if text:
                        self.voice_detected.emit(text)
                except sr.WaitTimeoutError:
                    pass
                except Exception as e:
                    pass
    
    def stop(self):
        self.running = False

class AIWorker(QThread):
    """Cerveau rapide (Ollama)"""
    response_ready = pyqtSignal(str)
    token_ready = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.ollama = OptimizedOllama()
        self.selector = SmartModelSelector(self.ollama)
        self.cache = SmartCache()
        self.query = None
    
    def set_query(self, query):
        self.query = query
    
    def run(self):
        if not self.query: return
        
        # Check Cache
        if self.cache.is_cacheable(self.query):
            cached = self.cache.get(self.query)
            if cached:
                self.response_ready.emit(cached)
                return
        
        # Streaming Chat
        full_response = ""
        try:
            for token in self.selector.smart_chat(self.query):
                full_response += token
                self.token_ready.emit(token)
            
            if self.cache.is_cacheable(self.query):
                self.cache.set(self.query, full_response)
            
            self.response_ready.emit(full_response)
        except Exception as e:
            self.response_ready.emit(f"Erreur IA: {e}")

class SoniaAgent:
    def __init__(self):
        logger.info("🤖 Initializing Sonia...")
        self.app = QApplication(sys.argv)
        
        # 1. UI (HUD)
        self.hud = OptimizedHUD("hud_icon.png")
        
        # 2. Sortie Vocale (TTS)
        self.tts = StreamingTTS()
        self.streaming_ai = StreamingAI(self.tts)
        
        # 3. Workers
        self.voice_worker = VoiceWorker()
        self.ai_worker = AIWorker()
        self.exec_worker = ExecutionWorker()
        self.sentinel_worker = SentinelWorker()
        self.telegram_worker = TelegramWorker()
        
        # Connexions Signaux
        
        # Entrée Vocale
        self.voice_worker.voice_detected.connect(self.on_voice_input)
        
        # IA Rapide (Chat)
        self.ai_worker.token_ready.connect(self.streaming_ai.process_token)
        self.ai_worker.response_ready.connect(self.on_ai_complete)
        
        # Exécution Système (Action)
        self.exec_worker.log_output.connect(self.on_exec_log)
        self.exec_worker.finished.connect(self.on_exec_finished)
        
        # Surveillance (Sentinel)
        self.sentinel_worker.alert.connect(self.speak_alert)
        
        # Telegram
        self.telegram_worker.message_received.connect(self.on_telegram_message)
        
        # État
        self.wake_words = ["sonia", "soignat", "sonya", "sonja"] # Common mishearings
        self.is_processing = False

    def start(self):
        self.hud.show()
        
        # Démarrage des threads
        self.voice_worker.start()
        self.sentinel_worker.start()
        self.telegram_worker.start()
        
        self.tts.speak_immediate("Sonia Online. I'm listening.")
        logger.success("✅ Sonia Started")
        
        sys.exit(self.app.exec())

    def on_voice_input(self, text):
        logger.debug(f"👂 Heard: {text}")
        
        # Wake Word Check
        text_lower = text.lower()
        if not any(w in text_lower for w in self.wake_words) and not self.is_processing:
            return
            
        # Clean text
        clean_text = text
        for w in self.wake_words:
            clean_text = clean_text.replace(w, "", 1).strip() # Case sensitive replace issue? better regex?
            # Simple fix for now
            if text_lower.startswith(w):
                 clean_text = text[len(w):].strip()
        
        if not clean_text:
            self.tts.speak_immediate("Yes?")
            return
            
        self.process_command(clean_text)

    def on_telegram_message(self, text):
        logger.info(f"✈️ Telegram: {text}")
        self.process_command(text, source="telegram")

    def process_command(self, command, source="voice"):
        if self.is_processing and source == "voice": return
        
        self.is_processing = True
        self.hud.set_state("thinking")
        
        # ROUTING LOGIC (The Brain)
        # Déterminer si c'est une action ou une discussion
        action_keywords = ["open", "run", "make", "delete", "close", "create", "search", "set"]
        
        is_action = any(k in command.lower() for k in action_keywords)
        
        if is_action:
            logger.info(f"⚙️ Routing to Execution: {command}")
            self.tts.speak_immediate("I'm on it.")
            self.exec_worker.set_command(command)
            self.exec_worker.start()
        else:
            logger.info(f"🧠 Routing to AI: {command}")
            self.streaming_ai.reset() # Reset streaming state
            self.ai_worker.set_query(command)
            self.ai_worker.start()

    def on_ai_complete(self, response):
        logger.info("✅ AI Response Complete")
        self.streaming_ai.flush_buffer()
        
        # FIX: Check if we actually spoke anything via streaming
        if response and not self.streaming_ai.has_spoken:
             logger.info(f"🗣️ Speaking full response (Cache/Direct): {response}")
             self.tts.speak_immediate(response)
        
        self.streaming_ai.flush_buffer()
        self.hud.set_state("speaking")
        QTimer.singleShot(2000, self.reset_state)

    def on_exec_log(self, log):
        logger.debug(log)
        # On pourrait afficher ça dans le terminal ou une fenêtre de debug

    def on_exec_finished(self, summary):
        logger.success(f"✅ Execution Finished: {summary}")
        self.tts.speak_immediate(summary)
        self.hud.set_state("speaking")
        QTimer.singleShot(2000, self.reset_state)

    def speak_alert(self, text):
        logger.warning(f"🚨 Alert: {text}")
        self.tts.speak_immediate(text)
        # Envoi Telegram aussi ?
        self.telegram_worker.send_message(f"🚨 Alerte BOB: {text}")

    def reset_state(self):
        self.is_processing = False
        self.hud.set_state("idle")

if __name__ == "__main__":
    try:
        sonia = SoniaAgent()
        sonia.start()
    except KeyboardInterrupt:
        sys.exit()

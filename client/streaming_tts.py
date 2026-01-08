import asyncio
import re
import edge_tts
import pygame
import tempfile
import os
from queue import Queue
import threading

class StreamingTTS:
    def __init__(self, voice="en-US-AriaNeural"):
        self.voice = voice
        self.audio_queue = Queue()
        self.playback_queue = Queue() # Initialisation ici pour éviter race condition
        self.is_speaking = False
        pygame.mixer.init(frequency=24000)
        
        # Démarrer worker thread pour TTS
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
        
        # Démarrer worker thread pour playback
        self.playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self.playback_thread.start()
    
    def _split_sentences(self, text):
        """Divise le texte en phrases pour streaming"""
        # Patterns pour détecter fin de phrase
        sentence_endings = re.compile(r'(?<=[.!?])\s+|(?<=\.)\s*$')
        sentences = sentence_endings.split(text.strip())
        return [s.strip() for s in sentences if s.strip()]
    
    def _tts_worker(self):
        """Worker thread pour génération TTS"""
        while True:
            try:
                text = self.audio_queue.get()
                if text is None:  # Signal d'arrêt
                    break
                
                # Emoji Cleaning: Remove non-standard characters to prevent TTS issues
                clean_text = text.encode('ascii', 'ignore').decode('ascii')
                clean_text = clean_text.strip()
                
                if not clean_text:
                    self.audio_queue.task_done()
                    continue

                # Générer audio avec EdgeTTS
                asyncio.run(self._generate_audio(clean_text))
                self.audio_queue.task_done()
            except Exception as e:
                print(f"TTS Error: {e}")
    
    async def _generate_audio(self, text):
        """Génère fichier audio pour une phrase"""
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tmp_path = tmp.name
            
            await communicate.save(tmp_path)
            
            # Ajouter à la queue de playback
            self.playback_queue.put(tmp_path)
        except Exception as e:
            print(f"Audio generation error: {e}")
    
    def _playback_worker(self):
        """Worker thread pour lecture audio séquentielle"""
        # self.playback_queue est déjà initialisée dans __init__
        
        while True:
            try:
                audio_file = self.playback_queue.get()
                if audio_file is None:  # Signal d'arrêt
                    break
                
                self.is_speaking = True
                
                # Jouer le fichier
                sound = pygame.mixer.Sound(audio_file)
                channel = sound.play()
                
                if channel:
                    # Attendre fin de lecture
                    while channel.get_busy():
                        pygame.time.wait(10)
                else:
                    print("Warning: No audio channel available to play sound.")
                
                # Nettoyer fichier temporaire
                try:
                    os.unlink(audio_file)
                except:
                    pass
                
                self.is_speaking = False
                self.playback_queue.task_done()
                
            except Exception as e:
                print(f"Playback error: {e}")
                self.is_speaking = False
                # Ensure task_done is called even on error if we got an item
                try:
                    self.playback_queue.task_done()
                except ValueError:
                    pass
    
    def speak_streaming(self, text):
        """Parle en streaming - divise en phrases et génère en parallèle"""
        sentences = self._split_sentences(text)
        
        for sentence in sentences:
            if sentence:
                self.audio_queue.put(sentence)
    
    def speak_immediate(self, text):
        """Parle immédiatement (pour réponses courtes)"""
        self.audio_queue.put(text)
    
    def stop(self):
        """Arrête tous les workers"""
        self.audio_queue.put(None)
        self.playback_queue.put(None)

class StreamingAI:
    """Simule IA qui génère du texte en streaming"""
    
    def __init__(self, tts_engine):
        self.tts = tts_engine
        self.current_buffer = ""
        self.has_spoken = False

    def reset(self):
        """Reset state for new generation"""
        self.current_buffer = ""
        self.has_spoken = False
    
    def process_token(self, token):
        """Traite chaque token généré par l'IA"""
        self.current_buffer += token
        
        # Détecter fin de phrase (ou retour à la ligne)
        # Optimisation "Temps Réel": On coupe aussi sur les virgules si le buffer est assez long
        # pour éviter d'attendre la fin d'une longue phrase complexe.
        is_sentence_end = any(p in token for p in ['.', '!', '?', '\n'])
        is_sub_clause = any(p in token for p in [',', ':', ';'])
        
        should_speak = False
        if is_sentence_end:
            should_speak = True
        elif is_sub_clause and len(self.current_buffer) > 40: # ~6-8 mots
            should_speak = True
            
        if should_speak:
            sentence = self.current_buffer.strip()
            if sentence and len(sentence) > 2: # Avoid speaking single chars
                if not self.has_spoken:
                     print(f"⏱️ First Audio Triggered")
                print(f"Speaking: {sentence}")
                self.tts.speak_immediate(sentence)
                self.current_buffer = ""
                self.has_spoken = True
    
    def flush_buffer(self):
        """Parle le reste du buffer"""
        if self.current_buffer.strip():
            print(f"Flushing: {self.current_buffer.strip()}")
            self.tts.speak_immediate(self.current_buffer.strip())
            self.current_buffer = ""
            self.has_spoken = True

# Exemple d'usage
if __name__ == "__main__":
    import time
    
    # Initialiser TTS streaming
    tts = StreamingTTS()
    ai = StreamingAI(tts)
    
    # Simuler génération IA token par token
    response = "Bonjour ! Je suis en train de traiter votre demande. Cela peut prendre quelques secondes. Merci de patienter."
    
    print("Simulation streaming IA...")
    for i, char in enumerate(response):
        ai.process_token(char)
        time.sleep(0.05)  # Simule latence génération
    
    ai.flush_buffer()
    
    # Attendre fin de lecture
    time.sleep(5)
    tts.stop()
import requests
import json
import time
import datetime
import os
from groq_client import GroqClient

class OptimizedOllama:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.groq = GroqClient()
        
        # Hybrid Model Configuration
        # If Groq is available, we use it for SPEED.
        # Format: "groq/model_name" or "model_name" (for local Ollama)
        
        self.models = {
            "fast": "groq/llama3-8b-8192" if self.groq.client else "phi3:mini",
            "balanced": "groq/llama3-70b-8192" if self.groq.client else "phi3:mini",
            "smart": "groq/llama3-70b-8192" if self.groq.client else "phi3:mini",
            "coding": "groq/llama3-70b-8192" if self.groq.client else "phi3:mini"
        }
        
        self.current_model = "balanced"
    
    def set_model(self, model_type="fast"):
        """Change le modèle selon le besoin"""
        if model_type in self.models:
            self.current_model = model_type
            print(f"Switched to {model_type} model: {self.models[model_type]}")
            
    def chat_streaming(self, query, system_prompt=None, **kwargs):
        """Générateur qui stream la réponse token par token (Hybrid Groq/Ollama)"""
        
        model_name = self.models.get(self.current_model, "phi3:mini")
        
        # --- GROQ ROUTING ---
        if model_name.startswith("groq/"):
            real_model = model_name.replace("groq/", "")
            yield from self.groq.stream_chat(query, system_prompt, model=real_model, **kwargs)
            return

        # --- OLLAMA ROUTING (Fallback) ---
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt or "You are Sonia, a helpful assistant."},
                {"role": "user", "content": query}
            ],
            "stream": True
        }
        
        if kwargs:
            payload.update(kwargs)
            if "options" in kwargs: pass 

        try:
            with requests.post(url, json=payload, stream=True) as response:
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    token = data["message"]["content"]
                                    yield token
                            except:
                                pass
        except Exception as e:
            yield f"Error: {str(e)}"

class SmartModelSelector:
    def __init__(self, ollama_instance):
        self.ollama = ollama_instance
    
    def select_model_for_query(self, query):
        """Choisit le bon modèle selon la complexité"""
        q = query.lower()
        if any(w in q for w in ["code", "python", "function", "script", "bug"]):
            return "coding"
        elif any(w in q for w in ["why", "explain", "history", "complex"]):
            return "smart"
        elif len(q) < 20: 
            return "fast"
        return "balanced"

    def smart_chat(self, query):
        model_type = self.select_model_for_query(query)
        self.ollama.set_model(model_type)
        
        # System Prompt - Fluid & Fast (Direct & Natural)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        JARVIS_SYSTEM_PROMPT = f"""You are Sonia, a helpful AI.
Current Date: {now}
Interact naturally and fluidly.
- Be direct and concise.
- Provide clear answers.
- Use context."""
        
        # Options
        options = {
            "keep_alive": -1,
            "num_ctx": 4096, # Groq handles large context easily
            "temperature": 0.6,
            "top_k": 50,
            "top_p": 0.9,
        }
        return self.ollama.chat_streaming(query, JARVIS_SYSTEM_PROMPT, options=options)

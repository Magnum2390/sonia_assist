
import requests
import json
import time

class OptimizedOllama:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.models = {
            "fast": "phi3:mini",           # 3.8B - Ultra rapide
            "balanced": "mistral:7b",      # 7B - Bon compromis
            "smart": "mistral:7b",        # 8B - Plus intelligent
            "coding": "codellama:7b"       # 7B - Spécialisé code
        }
        self.current_model = "balanced"
    
    def set_model(self, model_type="fast"):
        """Change le modèle selon le besoin"""
        if model_type in self.models:
            self.current_model = model_type
            print(f"🔄 Switched to {model_type} model: {self.models[model_type]}")
            
    def chat_streaming(self, query, system_prompt=None):
        """Générateur qui stream la réponse token par token"""
        url = f"{self.base_url}/api/chat"
        
        # Sélection du modèle
        model_name = self.models.get(self.current_model, "mistral:7b")
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt or "You are Sonia, a helpful assistant."},
                {"role": "user", "content": query}
            ],
            "stream": True
        }
        
        try:
            with requests.post(url, json=payload, stream=True) as response:
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    token = data["message"]["content"]
                                    # print(f"DEBUG OLLAMA: {token}", flush=True)
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
        elif len(q) < 20: # Questions courtes
            return "fast"
        return "balanced"

    def smart_chat(self, query):
        model_type = self.select_model_for_query(query)
        self.ollama.set_model(model_type)
        
        # System Prompt
        JARVIS_SYSTEM_PROMPT = """You are Sonia, an advanced personal AI assistant. 
Answer in a concise, intelligent, and warm manner.
Be efficient and direct in your responses."""
        
        return self.ollama.chat_streaming(query, JARVIS_SYSTEM_PROMPT)

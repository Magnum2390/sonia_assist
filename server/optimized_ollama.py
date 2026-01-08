
import requests
import json
import time
import datetime

class OptimizedOllama:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.models = {
            "fast": "mistral-nemo",        # 12B - On veut la qualité Nemo tout le temps
            "balanced": "mistral-nemo",    # 12B
            "smart": "mistral-nemo",       # 12B
            "coding": "mistral-nemo"       # 12B - Nemo est bon en code aussi
        }
        self.current_model = "balanced"
    
    def set_model(self, model_type="fast"):
        """Change le modèle selon le besoin"""
        if model_type in self.models:
            self.current_model = model_type
            print(f"Switched to {model_type} model: {self.models[model_type]}")
            
    def chat_streaming(self, query, system_prompt=None, **kwargs):
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
        
        # Merge additional options (keep_alive, options dict, etc.)
        if kwargs:
            payload.update(kwargs)
            # Special handling if 'options' is passed as a dict inside kwargs
            if "options" in kwargs:
                 # Ensure it's merged correctly if needed, but Ollama API takes 'options' at top level too
                 pass
        
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
        elif len(q) < 20: # Questions courtes
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
        
        # Options: Aggressive Speed Tuning
        # keep_alive=-1 (Stay in RAM)
        # num_ctx=2048 (Low Context for Max Speed)
        # top_k=20 (Fast Sampling)
        options = {
            "keep_alive": -1,
            "num_ctx": 2048,
            "temperature": 0.5,
            "top_k": 20,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }
        return self.ollama.chat_streaming(query, JARVIS_SYSTEM_PROMPT, options=options)

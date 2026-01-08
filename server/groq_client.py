import os
from groq import Groq

class GroqClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
                print("[Groq] Client Initialized 🚀")
            except Exception as e:
                print(f"[Groq] Init Error: {e}")
        else:
            print("[Groq] No API Key found.")

    def stream_chat(self, query, system_prompt, model="llama3-8b-8192", **kwargs):
        """Streams response from Groq API"""
        if not self.client:
            yield "Error: Groq not configured."
            return

        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            
            # Map typical kwargs to Groq params if needed, or rely on defaults
            # Groq defaults are usually fine.
            
            stream = self.client.chat.completions.create(
                messages=messages,
                model=model,
                stream=True,
                temperature=kwargs.get('temperature', 0.6),
                max_tokens=kwargs.get('num_predict', 1024),
                top_p=kwargs.get('top_p', 0.9)
            )
            
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
                    
        except Exception as e:
            yield f"Groq Error: {str(e)}"

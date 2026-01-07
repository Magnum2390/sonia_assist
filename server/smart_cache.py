
import json
import os
from pathlib import Path

class SmartCache:
    def __init__(self, cache_file="cache/query_cache.json"):
        self.cache_file = cache_file
        self.cache = self._load_cache()
        
    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def get(self, query):
        """Récupère une réponse exacte si elle existe"""
        return self.cache.get(query.lower().strip())
    
    def set(self, query, response):
        """Sauvegarde une nouvelle paire Q/R"""
        if len(response) > 500: return # Don't cache long essays
        
        self.cache[query.lower().strip()] = response
        self._save_cache()
        
    def _save_cache(self):
        # Ensure dir exists
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def is_cacheable(self, query):
        # On ne cache pas les commandes dynamiques (heure, météo, news...)
        dynamic_words = ["time", "hour", "weather", "news", "date", "today", "now"]
        return not any(w in query.lower() for w in dynamic_words)
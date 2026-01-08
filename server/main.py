
from fastapi import FastAPI, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from optimized_ollama import OptimizedOllama, SmartModelSelector
from smart_cache import SmartCache
from interpreter import interpreter
import uvicorn
import asyncio
import os

# --- Configuration Open Interpreter ---
interpreter.offline = True
interpreter.llm.model = "ollama/mistral-nemo"
interpreter.llm.api_base = "http://localhost:11434"
interpreter.auto_run = True
interpreter.system_message = """
You are the Execution Engine for Sonia.
Your role is to ACT. Do not talk, just execute.

IMPORTANT: To run commands, you MUST use markdown code blocks.
Example:
```shell
echo "hello"
```
Do NOT use JSON tool calls. Just write the code in the block.
"""

# --- App Definition ---
app = FastAPI(title="Sonia Brain API", version="1.0")

# --- Services ---
ollama = OptimizedOllama()
selector = SmartModelSelector(ollama)
cache = SmartCache()
from command_registry import CommandRegistry
registry = CommandRegistry()

# --- Models ---
class ChatRequest(BaseModel):
    query: str
    source: str = "voice"

class CommandRequest(BaseModel):
    command: str

# --- Routes ---

@app.get("/status")
def status():
    return {"status": "online", "model": ollama.current_model}

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Streaming Chat Endpoint"""
    query = req.query
    print(f"[Brain] Received Query: {query}")
    
    # 1. Check Cache
    if cache.is_cacheable(query):
        cached = cache.get(query)
        if cached:
            print(f"[Brain] Cache Hit: {cached}")
            # Generator for cached response
            async def cached_stream():
                yield cached
            return StreamingResponse(cached_stream(), media_type="text/plain")

    # 2. Stream from Ollama
    async def generate_stream():
        full_resp = ""
        # Note: smart_chat returns a generator (blocking IO usually), we wrap it properly later
        # For now, simplistic sync generator iteration
        for token in selector.smart_chat(query):
             full_resp += token
             yield token
             await asyncio.sleep(0.01) # Yield control
             
        # Cache Result
        if cache.is_cacheable(query):
            cache.set(query, full_resp)
            
    return StreamingResponse(generate_stream(), media_type="text/plain")

@app.post("/execute")
def execute_endpoint(req: CommandRequest):
    """Execute System Command (Hybrid: Deterministic -> AI Fallback)"""
    cmd = req.command
    print(f"[Execution] Received: {cmd}")
    
    # 1. Try Deterministic Registry (The 90% Layer)
    direct_result = registry.match_and_execute(cmd)
    if direct_result:
        print(f"[Execution] Deterministic Match: {direct_result}")
        return {"status": "success", "summary": direct_result}

    # 2. Fallback to Open Interpreter (The 10% AI Layer)
    print(f"[Execution] No Match. Delegating to AI (Mistral-Nemo)...")
    try:
        # Interpreter chat returns a list of dicts
        result = interpreter.chat(cmd)
        
        summary = "Done."
        for msg in result:
             if msg.get('role') == 'assistant':
                 summary = msg.get('content')
        
        return {"status": "success", "summary": summary}
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

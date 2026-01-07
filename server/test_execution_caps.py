
from interpreter import interpreter

# Configuration basique pour tester
interpreter.offline = True 
interpreter.llm.model = "ollama/mistral:7b"
interpreter.llm.api_base = "http://localhost:11434"
interpreter.auto_run = True 

print(" Testing Open Interpreter Capabilities...")
try:
    # Action simple : lister le dossier courant
    print("Command: List files in current directory")
    messages = interpreter.chat("List files in the current directory and print them.")
    
    print("\n--- Result ---")
    for msg in messages:
        if msg.get('role') == 'computer':
            print(f"[Computer]: {msg.get('content')}")
        elif msg.get('role') == 'assistant':
            print(f"[Assistant]: {msg.get('content')}")
            
except Exception as e:
    print(f"CRITICAL ERROR: {e}")

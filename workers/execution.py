
from PyQt6.QtCore import QThread, pyqtSignal
from interpreter import interpreter
import sys

# Configuration initiale de l'interpréteur
interpreter.offline = True # Force le mode local
interpreter.llm.model = "ollama/mistral:7b"
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

class ExecutionWorker(QThread):
    """Thread dédié à l'exécution de commandes via Open Interpreter"""
    finished = pyqtSignal(str)
    log_output = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.command = None
        
    def set_command(self, command):
        self.command = command
        
    def run(self):
        if not self.command:
            return
            
        try:
            self.log_output.emit(f"🚀 Executing: {self.command}")
            
            # Exécution via Open Interpreter
            result = interpreter.chat(self.command)
            
            final_summary = "Terminé."
            full_report = []
            
            for msg in result:
                if msg.get('role') == 'assistant':
                    content = msg.get('content')
                    if content: 
                         final_summary = content
                
                if msg.get('role') == 'computer':
                    output = msg.get('content')
                    if output:
                        clean_output = output[:200] + "..." if len(output) > 200 else output
                        full_report.append(f"[Output]: {clean_output}")
                        self.log_output.emit(f"💻 {clean_output}")

            self.finished.emit(final_summary)
            
        except Exception as e:
            self.finished.emit(f"Erreur d'exécution: {str(e)}")
            self.log_output.emit(f"🔥 Error: {str(e)}")

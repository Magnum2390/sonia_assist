from PyQt6.QtCore import QThread, pyqtSignal
import requests

SERVER_URL = "http://localhost:8000"

class APIWorker(QThread):
    token_received = pyqtSignal(str)
    response_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.query = None
        self.endpoint = "/chat" # /chat or /execute
    
    def set_query(self, query, endpoint="/chat"):
        self.query = query
        self.endpoint = endpoint
        
    def run(self):
        if not self.query: return
        
        try:
            if self.endpoint == "/chat":
                # Streaming Response
                full_resp = ""
                import time
                start_req = time.time()
                first_token = True
                
                with requests.post(f"{SERVER_URL}/chat", json={"query": self.query}, stream=True) as r:
                    if r.status_code == 200:
                        for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
                            if chunk:
                                if first_token:
                                    ttft = time.time() - start_req
                                    print(f"⏱️ TTFT (Server): {ttft:.2f}s")
                                    first_token = False
                                
                                self.token_received.emit(chunk)
                                full_resp += chunk
                        self.response_complete.emit(full_resp)
                    else:
                        self.error_occurred.emit(f"Server Error: {r.status_code}")
            
            elif self.endpoint == "/execute":
                 # Execution (Blocking)
                 r = requests.post(f"{SERVER_URL}/execute", json={"command": self.query})
                 if r.status_code == 200:
                     data = r.json()
                     self.response_complete.emit(data.get("summary", "Done"))
                 else:
                     self.error_occurred.emit(f"Exec Error: {r.status_code}")
                     
        except Exception as e:
            self.error_occurred.emit(str(e))

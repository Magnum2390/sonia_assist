
import requests
import time
import os

SERVER_URL = "http://localhost:8000"
TARGET_FILE = "proof_of_life.txt"

def test_execution():
    print("Testing Open Interpreter Capability...")
    
    # 1. Clean up
    if os.path.exists(TARGET_FILE):
        os.remove(TARGET_FILE)
        
    # 2. Send Command
    command = f"Create a file named {TARGET_FILE} with the content 'Sonia is Alive'"
    print(f"Sending command: {command}")
    
    try:
        response = requests.post(f"{SERVER_URL}/execute", json={"command": command})
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.json()}")
    except Exception as e:
        print(f"Connection Failed: {e}")
        return

    # 3. Wait and Verify
    print("Waiting for execution...")
    for i in range(10):
        if os.path.exists(TARGET_FILE):
            print("✅ SUCCESS: File created!")
            with open(TARGET_FILE, 'r') as f:
                print(f"Content: {f.read()}")
            return
        time.sleep(1)
        print(".", end="", flush=True)
        
    print("\n❌ FAILURE: File not created in time.")

if __name__ == "__main__":
    test_execution()

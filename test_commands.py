import requests
import json
import time

BASE_URL = "http://localhost:8000/execute"

def test_cmd(command):
    print(f"\n--- Testing: '{command}' ---")
    try:
        resp = requests.post(BASE_URL, json={"command": command})
        if resp.status_code == 200:
            data = resp.json()
            print(f"Status: {data.get('status')}")
            print(f"Summary: {data.get('summary')}")
            
            # Heuristic to check if it used Registry or AI
            # Registry returns specific strings like "Volume increased."
            # AI (Mistral) usually returns "Done." or a longer sentence.
            summary = data.get('summary', '')
            if any(s in summary for s in ["Volume", "Notepad", "Calculator", "opened", "increased", "decreased"]):
                print("✅ Source: REGISTRY (Deterministic)")
            else:
                print("⚠️ Source: AI / FALLBACK (Unknown)")
        else:
            print(f"❌ HTTP Error: {resp.status_code}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    print("🧪 Starting Command Registry Tests...")
    time.sleep(1)
    
    test_cmd("Monte le volume")
    test_cmd("Volume à 25%")
    test_cmd("Ouvre le bloc-notes")
    
    # Music Tests
    test_cmd("Met de la musique")
    test_cmd("Pause la musique")
    test_cmd("Suivant")
    
    print("\nTests Complete.")

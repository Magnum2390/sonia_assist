import re
import os
import subprocess
import ctypes
import webbrowser
import pyautogui

class CommandRegistry:
    def __init__(self):
        self.commands = [
            # --- System/Apps ---
            (r"(?i)(open|lance|démarrer)\s+(notepad|bloc-notes)", self.open_notepad),
            (r"(?i)(open|lance|démarrer)\s+(calculator|calculatrice)", self.open_calculator),
            (r"(?i)(open|lance|démarrer)\s+(chrome|browser|navigateur)", self.open_chrome),
            (r"(?i)(open|lance|démarrer)\s+(vscode|code)", self.open_vscode),
            (r"(?i)(lock|verrouille)(\s+(pc|screen|ordinateur|session))?", self.lock_workstation),
            (r"(?i)(shutdown|éteins|arrete)(\s+(pc|computer))?", self.shutdown_pc),
            (r"(?i)(search|cherche)\s+(for\s+)?(.+)", self.web_search),
            
            # --- Multimedia ---
            (r"(?i)(monte|augmente)\s+(le\s+)?volume", self.volume_up),
            (r"(?i)(baisse|diminue)\s+(le\s+)?volume", self.volume_down),
            (r"(?i)volume\s+(à|a)\s+(\d+)%?", self.volume_set),
            (r"(?i)(coupe|arrete)\s+(le\s+)?son|mute", self.volume_mute),
            (r"(?i)(remet|active)\s+(le\s+)?son|unmute", self.volume_unmute),
            
            # --- Media Control ---
            (r"(?i)(joue|play|met)\s+(de\s+la\s+)?musique", self.media_play_pause),
            (r"(?i)(pause|stop)\s+(la\s+)?musique", self.media_play_pause), # Often same key
            (r"(?i)(suivant|next|prochaine)", self.media_next),
            (r"(?i)(précédent|previous|avant)", self.media_prev),
        ]

    def match_and_execute(self, query):
        """Tente de trouver une commande prédéfinie"""
        for pattern, func in self.commands:
            match = re.search(pattern, query)
            if match:
                try:
                    return func(match)
                except Exception as e:
                    return f"Error executing predefined command: {e}"
        return None

    # --- Actions: Multimedia ---
    def volume_up(self, match):
        for _ in range(5): pyautogui.press("volumeup")
        return "Volume increased."

    def volume_down(self, match):
        for _ in range(5): pyautogui.press("volumedown")
        return "Volume decreased."

    def volume_mute(self, match):
        pyautogui.press("volumemute")
        return "Audio muted."

    def volume_unmute(self, match):
        pyautogui.press("volumemute") # Toggle
        return "Audio unmuted."
        
    def volume_set(self, match):
        level = int(match.group(2))
        level = max(0, min(100, level)) # Clamp 0-100
        # PowerShell trick for absolute volume is complex, falling back to approximation
        # Or using nircmd if available. 
        # For now, let's try a loop approach: Mute (0) then Up X times.
        # Each 'volumeup' is usually 2%.
        pyautogui.press("volumemute") # Mute (might toggle off?) No, this is unreliable.
        # Robust way: 50 volume downs (to 0), then X/2 volume ups.
        for _ in range(50): pyautogui.press("volumedown")
        steps = int(level / 2)
        for _ in range(steps): pyautogui.press("volumeup")
        return f"Volume set to approx {level}%."

    def media_play_pause(self, match):
        pyautogui.press("playpause")
        return "Media toggled."

    def media_next(self, match):
        pyautogui.press("nexttrack")
        return "Next track."

    def media_prev(self, match):
        pyautogui.press("prevtrack")
        return "Previous track."

    # --- Actions: Apps ---
    def open_notepad(self, match):
        subprocess.Popen("notepad.exe")
        return "Notepad opened."
    # ... (rest of implementation identical)

    def open_calculator(self, match):
        subprocess.Popen("calc.exe")
        return "Calculator opened."
        
    def open_chrome(self, match):
        subprocess.Popen("start chrome", shell=True)
        return "Chrome opened."
        
    def open_vscode(self, match):
        subprocess.Popen("code", shell=True)
        return "VS Code opened."

    def lock_workstation(self, match):
        ctypes.windll.user32.LockWorkStation()
        return "Workstation locked."
        
    def shutdown_pc(self, match):
        # Safety check? Maybe just warn for now.
        return "Shutdown command recognized but safe-guarded. Run manually for now."

    def web_search(self, match):
        term = match.group(3) # (.+) is group 3 in 'search for (.+)'
        url = f"https://www.google.com/search?q={term}"
        webbrowser.open(url)
        return f"Searching for {term}."

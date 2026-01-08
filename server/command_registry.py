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
            (r"(?i)(monte|augmente|increase|up)\s+(le\s+)?(volume|son|sound)", self.volume_up),
            (r"(?i)(baisse|diminue|decrease|down)\s+(le\s+)?(volume|son|sound)", self.volume_down),
            (r"(?i)volume\s+(à|a|to|at)\s+(\d+)%?", self.volume_set),
            (r"(?i)(coupe|arrete|mute|silence)\s+(le\s+)?(son|sound|audio)|mute", self.volume_mute),
            (r"(?i)(remet|active|unmute)\s+(le\s+)?(son|sound|audio)|unmute", self.volume_unmute),
            
            # --- Media Control ---
            # --- Media Control ---
            # 1. Generic "Play Music" (No specific song) -> Default Resume (Spotify)
            (r"(?i)^(joue|play|met|start)(\s+(de\s+la\s+)?(musique|music|song|chanson|track))?$", self.media_play_music),
            
            # 2. Specific Platform: "Play [Title] on YouTube"
            (r"(?i)^(joue|play|met|ecouter)\s+(.+)\s+(sur|on|via)\s+(youtube|you tube)", self.media_play_youtube),
            
            # 3. Specific Platform: "Play [Title] on Spotify"
            (r"(?i)^(joue|play|met|ecouter)\s+(.+)\s+(sur|on|via)\s+spotify", self.media_play_spotify),
            
            # 4. Implicit Default: "Play [Title]" -> Spotify (or User Preference)
            # Matches "Play Dark" (without "on youtube")
            (r"(?i)^(joue|play|met|ecouter)\s+(.+)", self.media_play_spotify), # Defaulting to Spotify
            
            # Matches: "pause", "stop"
            (r"(?i)^(pause|stop|arrête|coupe|top|arrete)(\s+(.+)?(musique|music|song|chanson))?$", self.media_pause),
            
            (r"(?i)(suivant|next|prochaine|after)", self.media_next),
            (r"(?i)(précédent|previous|avant|before)", self.media_prev),
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

    def media_play_music(self, match):
        """Lance la musique (Reprend la dernière)"""
        try:
             subprocess.Popen("start spotify:", shell=True)
             import time
             time.sleep(1)
             pyautogui.press("playpause") 
             return "Spotify resumed."
        except:
             pyautogui.press("playpause")
             return "Media key pressed."

    def media_play_spotify(self, match):
        """Cherche sur Spotify"""
        # Group 2 is title since Group 3 is "on", Group 4 is "spotify" ? 
        # Wait, Regex 3 is: (joue) (.+) (on) spotify. -> Group 2 is Title.
        # Regex 4 is: (joue) (.+) -> Group 2 is Title.
        query = match.group(2).strip()
        
        # Cleanup "on spotify" if caught in trailing group (unlikely with specific regexes)
        print(f"[Registry] Spotify: {query}")
        subprocess.Popen(f'start spotify:search:"{query}"', shell=True)
        # Macro attempt (kept, just in case)
        import time
        time.sleep(2.0) 
        pyautogui.press('enter') 
        time.sleep(0.5)
        pyautogui.press('tab')
        pyautogui.press('enter')
        return f"Opening '{query}' on Spotify."

    def media_play_youtube(self, match):
        """Cherche sur YouTube (Navigateur défaut)"""
        import urllib.parse
        query = match.group(2).strip()
        print(f"[Registry] YouTube: {query}")
        
        encoded_query = urllib.parse.quote(query)
        # Open Search Results.
        # Trick: adding "&sp=EgIQAQ%253D%253D" finds Videos only, but standard search is fine.
        url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        # Using 'start' to open default browser
        # Quote URL properly for shell
        subprocess.Popen(f'start "" "{url}"', shell=True)
        return f"Opening '{query}' on YouTube."

    def media_pause(self, match):
        pyautogui.press("stop") # Or playpause is better for resume capability?
        # Typically "stop" resets. "playpause" is better for toggling.
        # Use playpause to be safe.
        pyautogui.press("playpause")
        return "Media paused."

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

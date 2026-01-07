
from PyQt6.QtCore import QThread, pyqtSignal
import psutil
import time
import datetime
import pythoncom
import win32com.client

class SentinelWorker(QThread):
    """Thread de surveillance système et alertes"""
    alert = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.last_cpu_alert = 0
        self.last_battery_alert = 0
        self.last_email_alert = 0
        self.last_briefing_date = None
        
    def run(self):
        # Initialisation COM dans le thread
        pythoncom.CoInitialize()
        
        while self.running:
            try:
                now = time.time()
                
                # 1. CPU Monitor (Check every 30s)
                self.check_cpu(now)
                
                # 2. Battery Monitor
                self.check_battery(now)
                
                # 3. Outlook Monitor (Check every 15 min)
                self.check_outlook(now)
                
                # 4. Morning Briefing
                self.check_briefing()
                
                # Sleep intelligent
                self.sleep(5) 
                
            except Exception as e:
                print(f"Sentinel Error: {e}")
                self.sleep(10)
                
        pythoncom.CoUninitialize()

    def check_cpu(self, now):
        cpu_percent = psutil.cpu_percent(interval=None)
        if cpu_percent > 85 and (now - self.last_cpu_alert > 300):
            self.alert.emit(f"Attention, charge CPU élevée à {cpu_percent} pourcent.")
            self.last_cpu_alert = now

    def check_battery(self, now):
        battery = psutil.sensors_battery()
        if battery:
            if battery.percent < 20 and not battery.power_plugged and (now - self.last_battery_alert > 300):
                self.alert.emit(f"Batterie faible à {battery.percent} pourcent. Veuillez brancher le secteur.")
                self.last_battery_alert = now

    def check_outlook(self, now):
        if (now - self.last_email_alert > 900): # 15 minutes
            try:
                outlook = win32com.client.Dispatch("Outlook.Application")
                namespace = outlook.GetNamespace("MAPI")
                inbox = namespace.GetDefaultFolder(6) # 6 = Inbox
                
                items = inbox.Items
                items.Sort("[ReceivedTime]", True) # Descending
                
                unread_count = 0
                last_sender = "Inconnu"
                
                # Scan top 20
                for i in range(1, 21):
                    try:
                        msg = items.Item(i)
                        if msg.UnRead:
                            unread_count += 1
                            if unread_count == 1:
                                last_sender = msg.SenderName
                    except: pass
                
                if unread_count > 0:
                    self.alert.emit(f"Vous avez {unread_count} emails non lus. Le dernier vient de {last_sender}.")
                    self.last_email_alert = now
            except:
                pass

    def check_briefing(self):
        dt_now = datetime.datetime.now()
        current_date = dt_now.strftime("%Y-%m-%d")
        current_time = dt_now.strftime("%H:%M")
        
        if current_time == "08:00" and self.last_briefing_date != current_date:
            self.alert.emit("Bonjour. Il est 8 heures. Tous les systèmes sont opérationnels.")
            self.last_briefing_date = current_date

    def stop(self):
        self.running = False

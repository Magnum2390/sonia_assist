
from PyQt6.QtCore import QThread, pyqtSignal
import asyncio
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from loguru import logger
import psutil
import ctypes

class TelegramWorker(QThread):
    """Thread gérant le bot Telegram"""
    message_received = pyqtSignal(str) # Émet le texte reçu pour traitement par Sonia
    request_screenshot = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.allowed_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.loop = None
        self.app = None

    def run(self):
        if not self.token or not self.allowed_chat_id:
            print("[Telegram] Config Missing")
            return

        # Créer une nouvelle boucle d'événements pour ce thread
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        self.loop.run_until_complete(self.start_bot())

    async def start_bot(self):
        self.app = ApplicationBuilder().token(self.token).build()
        
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("lock", self.cmd_lock))
        self.app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_message))
        
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        
        print("[Telegram] Worker Started")
        
        # Garder le thread en vie
        while self.running:
            await asyncio.sleep(1)
            
        await self.app.stop()

    async def check_auth(self, update: Update):
        if not update.effective_user: return False
        if str(update.effective_user.id) != str(self.allowed_chat_id).strip():
            return False
        return True

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_auth(update): return
        await context.bot.send_message(chat_id=update.effective_chat.id, text="**Sonia Online**")

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_auth(update): return
        cpu = psutil.cpu_percent()
        bat = psutil.sensors_battery()
        msg = f"CPU: {cpu}%\nBattery: {bat.percent if bat else 'AC'}%"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)

    async def cmd_lock(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_auth(update): return
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Locking workstation...")
        ctypes.windll.user32.LockWorkStation()

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_auth(update): return
        text = update.message.text
        # Envoie le texte au cerveau principal via signal
        self.message_received.emit(text)
        # On pourrait implémenter une réponse en retour si on connecte un signal inverse

    def send_message(self, text):
        """Méthode thread-safe pour envoyer un message"""
        if self.app and self.loop:
            asyncio.run_coroutine_threadsafe(
                self.app.bot.send_message(chat_id=self.allowed_chat_id, text=text),
                self.loop
            )

    def stop(self):
        self.running = False

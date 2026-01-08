import sys
import math
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QTransform, QColor

class AIWorker(QThread):
    """Thread séparé pour les calculs IA"""
    response_ready = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.command = None
        
    def set_command(self, cmd):
        self.command = cmd
        
    def run(self):
        if self.command:
            import time
            time.sleep(0.5)  # Remplacer par vraie requête API
            self.response_ready.emit(f"Processed: {self.command}")

class OptimizedHUD(QWidget):
    def __init__(self, image_path):
        super().__init__()
        
        self.original_pixmap = QPixmap(image_path)
        self.angle = 0
        self.state = "idle"  # idle, thinking, speaking
        self.setFixedSize(200, 200)
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Animation TOUJOURS dans main thread
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate_image)
        self.timer.start(16)  # 60 FPS
        
        # Worker thread pour IA
        self.ai_worker = AIWorker()
        self.ai_worker.response_ready.connect(self.on_ai_response)
        
        self.center_on_screen()

    def set_state(self, state):
        """Change l'état du HUD"""
        self.state = state
        if state == "thinking":
            self.timer.start(8)  # Plus rapide
        elif state == "speaking":
            self.timer.start(12)
        elif state == "listening_active":
            self.timer.start(14) # Un peu plus rapide que idle
        else:
            self.timer.start(16)
    
    def process_command(self, command):
        """Lance traitement IA dans thread séparé"""
        self.set_state("thinking")
        self.ai_worker.set_command(command)
        self.ai_worker.start()
    
    def on_ai_response(self, response):
        """Callback IA fini"""
        self.set_state("speaking")
        QTimer.singleShot(2000, lambda: self.set_state("idle"))

    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def rotate_image(self):
        self.angle = (self.angle + 1) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center = QPointF(self.width() / 2, self.height() / 2)
        transform = QTransform()
        transform.translate(center.x(), center.y())
        transform.rotate(self.angle)
        transform.translate(-center.x(), -center.y())
        
        painter.setTransform(transform)
        
        # Couleur selon état
        if self.state == "thinking":
            painter.setOpacity(0.8)
        elif self.state == "speaking":
            painter.setOpacity(1.0)
        elif self.state == "listening_active":
            painter.setOpacity(1.0)
            # Pulsation Logic based on angle (0-360)
            # Fait varier la taille entre 70 et 85 (plus petit que l'icone qui est ~100)
            # ou juste autour.
            import math
            pulse = (math.sin(math.radians(self.angle * 4)) + 1) / 2 # 0 to 1
            radius = 45 + (pulse * 5) # Varie entre 45 et 50 (Beaucoup plus discret)
            
            painter.setPen(Qt.PenStyle.NoPen)
            # Rouge vif avec transparence variable
            color = QColor(255, 69, 0)
            color.setAlpha(int(150 + (pulse * 50))) # 150-200 alpha
            painter.setBrush(color)
            
            # On dessine sans transformation de rotation pour le cercle (optionnel, mais plus propre)
            painter.resetTransform() 
            painter.drawEllipse(center, radius, radius)
            # Remettre la transfo pour l'image qui tourne
            painter.setTransform(transform)
            
        else:
            painter.setOpacity(0.6)
            
        # Calculate offset to center the image
        img_w = self.original_pixmap.width()
        img_h = self.original_pixmap.height()
        
        # Scale to fit while preserving aspect ratio
        scale_factor = min((self.width() - 50) / img_w, (self.height() - 50) / img_h)
        
        scaled_w = img_w * scale_factor
        scaled_h = img_h * scale_factor
        
        # Center horizontally and vertically
        x_offset = (self.width() - scaled_w) / 2
        y_offset = (self.height() - scaled_h) / 2

        painter.drawPixmap(
            QRectF(x_offset, y_offset, scaled_w, scaled_h),
            self.original_pixmap,
            QRectF(0, 0, img_w, img_h)
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    hud = OptimizedHUD("hud_icon.png")
    hud.show()
    sys.exit(app.exec())
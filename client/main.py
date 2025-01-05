import sys
import threading
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl

from app import create_app  # Die Flask-App importieren

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scandy")
        self.setMinimumSize(1200, 800)
        
        # Browser-Widget erstellen
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)
        
        # Flask-App URL laden
        self.browser.setUrl(QUrl("http://localhost:5000"))

def run_flask():
    """Startet den Flask-Server"""
    app = create_app()
    app.run(host="localhost", port=5000)

def main():
    # Flask-Server in einem separaten Thread starten
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True  # Thread wird beendet wenn Hauptprogramm endet
    flask_thread.start()
    
    # Qt-Anwendung starten
    qt_app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(qt_app.exec())

if __name__ == "__main__":
    main() 
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt

class AboutView(QWidget):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.init_ui()
        
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Über Scandy Container
        about_container = QFrame()
        about_container.setObjectName("table-container")
        about_layout = QVBoxLayout(about_container)
        
        # Titel
        title = QLabel("Über Scandy")
        title.setObjectName("section-header")
        about_layout.addWidget(title)
        
        # Beschreibung
        desc = QLabel(
            "Scandy ist ein modernes Werkzeug- und Materialverwaltungssystem, "
            "das speziell für die Bedürfnisse des BTZ Köln entwickelt wurde."
        )
        desc.setWordWrap(True)
        about_layout.addWidget(desc)
        
        layout.addWidget(about_container)
        
        # Features Container
        features_container = QFrame()
        features_container.setObjectName("table-container")
        features_layout = QVBoxLayout(features_container)
        
        # Features Titel
        features_title = QLabel("Features")
        features_title.setObjectName("section-header")
        features_layout.addWidget(features_title)
        
        # Feature Liste
        features = [
            "Barcode-basierte Werkzeugverwaltung",
            "Materialbestandsführung",
            "Mitarbeiterverwaltung",
            "Schnelle Ausleihe und Rückgabe",
            "Übersichtliche Statistiken",
            "Offline-Fähigkeit"
        ]
        
        for feature in features:
            label = QLabel(f"• {feature}")
            features_layout.addWidget(label)
            
        layout.addWidget(features_container)
        
        # Version
        version = QLabel("Version 1.0.0")
        version.setObjectName("footer-text")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version) 
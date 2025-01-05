from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt

class IndexView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Statistik-Karten
        stats_container = QWidget()
        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setSpacing(20)
        
        # Werkzeug-Statistiken
        tools_card = self.create_stats_card(
            "Werkzeuge",
            {
                "Gesamt": "120",
                "Verfügbar": "95",
                "Ausgeliehen": "20",
                "Defekt": "5"
            }
        )
        stats_layout.addWidget(tools_card)
        
        # Verbrauchsmaterial-Statistiken
        consumables_card = self.create_stats_card(
            "Verbrauchsmaterial",
            {
                "Gesamt": "45",
                "Verfügbar": "38",
                "Nachbestellen": "7"
            }
        )
        stats_layout.addWidget(consumables_card)
        
        # Mitarbeiter-Statistiken
        workers_card = self.create_stats_card(
            "Mitarbeiter",
            {
                "Gesamt": "50",
                "Aktiv": "48",
                "Inaktiv": "2"
            }
        )
        stats_layout.addWidget(workers_card)
        
        layout.addWidget(stats_container)
        
        # Quick Guide
        guide_container = QFrame()
        guide_container.setObjectName("guide-container")
        guide_layout = QVBoxLayout(guide_container)
        
        guide_title = QLabel("Quick Guide")
        guide_title.setObjectName("guide-title")
        guide_layout.addWidget(guide_title)
        
        steps_grid = QGridLayout()
        steps_grid.setSpacing(20)
        
        steps = [
            ("1", "Werkzeug scannen", "Scannen Sie den Barcode des Werkzeugs"),
            ("2", "Mitarbeiter scannen", "Scannen Sie den Barcode des Mitarbeiters"),
            ("3", "Status prüfen", "Überprüfen Sie den Ausleihstatus"),
            ("4", "Bestätigen", "Bestätigen Sie die Ausleihe/Rückgabe")
        ]
        
        for i, (number, title, description) in enumerate(steps):
            step_frame = QFrame()
            step_frame.setObjectName("step-frame")
            step_layout = QHBoxLayout(step_frame)
            
            number_label = QLabel(number)
            number_label.setObjectName("step-number")
            step_layout.addWidget(number_label)
            
            text_container = QFrame()
            text_layout = QVBoxLayout(text_container)
            
            title_label = QLabel(title)
            title_label.setObjectName("step-title")
            text_layout.addWidget(title_label)
            
            desc_label = QLabel(description)
            desc_label.setObjectName("step-description")
            text_layout.addWidget(desc_label)
            
            step_layout.addWidget(text_container)
            steps_grid.addWidget(step_frame, i // 2, i % 2)
            
        guide_layout.addLayout(steps_grid)
        layout.addWidget(guide_container)
        
    def create_stats_card(self, title, stats):
        """Erstellt eine Statistik-Karte"""
        card = QFrame()
        card.setObjectName("stats-card")
        layout = QVBoxLayout(card)
        
        # Titel
        title_label = QLabel(title)
        title_label.setObjectName("card-title")
        layout.addWidget(title_label)
        
        # Statistiken
        for key, value in stats.items():
            stat_container = QFrame()
            stat_layout = QHBoxLayout(stat_container)
            
            key_label = QLabel(key)
            key_label.setObjectName("stat-key")
            stat_layout.addWidget(key_label)
            
            value_label = QLabel(value)
            value_label.setObjectName("stat-value")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            stat_layout.addWidget(value_label)
            
            layout.addWidget(stat_container)
            
        return card 
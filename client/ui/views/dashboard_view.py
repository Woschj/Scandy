from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QGridLayout
from PyQt6.QtCore import Qt

class DashboardView(QWidget):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.init_ui()
        
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Statistik-Grid
        grid = QGridLayout()
        grid.setSpacing(20)
        
        # Werkzeug-Statistiken
        tools_stats = self.create_stats_card(
            "Werkzeuge",
            self.client.get_tool_stats(),
            "Gesamt",
            ["Verfügbar", "Ausgeliehen", "Defekt"]
        )
        grid.addWidget(tools_stats, 0, 0)
        
        # Material-Statistiken
        consumables_stats = self.create_stats_card(
            "Verbrauchsmaterial",
            self.client.get_consumables_stats(),
            "Gesamt",
            ["Verfügbar", "Nachbestellen"]
        )
        grid.addWidget(consumables_stats, 0, 1)
        
        # Mitarbeiter-Statistiken
        workers_stats = self.create_stats_card(
            "Mitarbeiter",
            self.client.get_worker_stats(),
            "Gesamt",
            ["Aktiv", "Inaktiv"]
        )
        grid.addWidget(workers_stats, 1, 0)
        
        layout.addLayout(grid)
        layout.addStretch()
        
    def create_stats_card(self, title, stats, total_key, detail_keys):
        """Erstellt eine Statistik-Karte"""
        card = QFrame()
        card.setObjectName("table-container")
        layout = QVBoxLayout(card)
        
        # Titel
        title_label = QLabel(title)
        title_label.setObjectName("section-header")
        layout.addWidget(title_label)
        
        # Gesamtzahl
        if total_key in stats:
            total = QLabel(f"{stats[total_key]} {total_key}")
            total.setObjectName("badge-info")
            layout.addWidget(total)
        
        # Details
        for key in detail_keys:
            if key in stats:
                detail = QFrame()
                detail_layout = QGridLayout(detail)
                detail_layout.setContentsMargins(0, 5, 0, 5)
                
                label = QLabel(key)
                detail_layout.addWidget(label, 0, 0)
                
                value = QLabel(str(stats[key]))
                value.setObjectName("badge-success")
                value.setAlignment(Qt.AlignmentFlag.AlignRight)
                detail_layout.addWidget(value, 0, 1)
                
                layout.addWidget(detail)
        
        return card 
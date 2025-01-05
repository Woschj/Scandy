from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame,
                               QPushButton, QLineEdit, QComboBox)
from PyQt6.QtCore import Qt

class ManualLoanView(QWidget):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.init_ui()
        
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Formular Container
        form_container = QFrame()
        form_container.setObjectName("table-container")
        form_layout = QVBoxLayout(form_container)
        
        # Titel
        title = QLabel("Manuelle Ausleihe")
        title.setObjectName("section-header")
        form_layout.addWidget(title)
        
        # Mitarbeiter
        worker_label = QLabel("Mitarbeiter")
        form_layout.addWidget(worker_label)
        
        self.worker_input = QComboBox()
        self.worker_input.setObjectName("filter-select")
        self.worker_input.addItem("Mitarbeiter auswählen...")
        # TODO: Mitarbeiter aus der Datenbank laden
        form_layout.addWidget(self.worker_input)
        
        # Werkzeug
        tool_label = QLabel("Werkzeug")
        form_layout.addWidget(tool_label)
        
        self.tool_input = QComboBox()
        self.tool_input.setObjectName("filter-select")
        self.tool_input.addItem("Werkzeug auswählen...")
        # TODO: Verfügbare Werkzeuge aus der Datenbank laden
        form_layout.addWidget(self.tool_input)
        
        # Ausleihen Button
        loan_btn = QPushButton("Ausleihen")
        loan_btn.setObjectName("primary-button")
        loan_btn.clicked.connect(self.loan_tool)
        form_layout.addWidget(loan_btn)
        
        layout.addWidget(form_container)
        layout.addStretch()
        
    def loan_tool(self):
        """Leiht ein Werkzeug aus"""
        # TODO: Implementiere die Ausleih-Logik
        pass 
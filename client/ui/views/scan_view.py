from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame
)
from PyQt6.QtCore import Qt

class ScanView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Scan Container
        scan_container = QFrame()
        scan_container.setObjectName("scan-container")
        scan_layout = QVBoxLayout(scan_container)
        scan_layout.setSpacing(20)
        
        # Titel
        title = QLabel("Barcode Scanner")
        title.setObjectName("scan-title")
        scan_layout.addWidget(title)
        
        # Scan-Bereich
        scan_section = QFrame()
        scan_section.setObjectName("scan-section")
        section_layout = QVBoxLayout(scan_section)
        
        # Scan-Input
        input_container = QFrame()
        input_container.setObjectName("input-container")
        input_layout = QVBoxLayout(input_container)
        
        scan_label = QLabel("Barcode scannen oder eingeben:")
        self.scan_input = QLineEdit()
        self.scan_input.setPlaceholderText("Barcode...")
        self.scan_input.returnPressed.connect(self.handle_scan)
        
        input_layout.addWidget(scan_label)
        input_layout.addWidget(self.scan_input)
        
        section_layout.addWidget(input_container)
        
        # Status-Anzeige
        self.status_label = QLabel()
        self.status_label.setObjectName("scan-status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.hide()
        section_layout.addWidget(self.status_label)
        
        scan_layout.addWidget(scan_section)
        
        # Info-Bereich
        info_container = QFrame()
        info_container.setObjectName("info-container")
        info_layout = QVBoxLayout(info_container)
        
        # Aktueller Scan
        current_scan = QFrame()
        current_scan.setObjectName("current-scan")
        current_layout = QVBoxLayout(current_scan)
        
        self.current_label = QLabel("Kein aktiver Scan")
        self.current_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        current_layout.addWidget(self.current_label)
        
        info_layout.addWidget(current_scan)
        
        # Letzte Scans
        history = QFrame()
        history.setObjectName("scan-history")
        history_layout = QVBoxLayout(history)
        
        history_title = QLabel("Letzte Scans")
        history_title.setObjectName("history-title")
        history_layout.addWidget(history_title)
        
        self.history_list = QVBoxLayout()
        history_layout.addLayout(self.history_list)
        
        info_layout.addWidget(history)
        
        scan_layout.addWidget(info_container)
        
        layout.addWidget(scan_container)
        
    def handle_scan(self):
        """Verarbeitet einen gescannten Barcode"""
        barcode = self.scan_input.text().strip()
        if not barcode:
            return
            
        # Status anzeigen
        self.status_label.setText(f"Barcode gescannt: {barcode}")
        self.status_label.setObjectName("scan-status-success")
        self.status_label.show()
        
        # Aktuellen Scan aktualisieren
        self.current_label.setText(f"Aktueller Scan: {barcode}")
        
        # Zur Historie hinzufügen
        history_item = QLabel(f"Scan: {barcode}")
        self.history_list.insertWidget(0, history_item)
        
        # Input leeren
        self.scan_input.clear()
        
        # Maximal 5 Einträge in der Historie
        while self.history_list.count() > 5:
            item = self.history_list.takeAt(self.history_list.count() - 1)
            if item.widget():
                item.widget().deleteLater() 
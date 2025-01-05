from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame,
    QHeaderView
)
from PyQt6.QtCore import Qt

class WorkersView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Filter Container
        filter_container = QFrame()
        filter_container.setObjectName("filter-container")
        filter_layout = QHBoxLayout(filter_container)
        
        # Suchfeld
        self.search_input = QLineEdit()
        self.search_input.setObjectName("search-input")
        self.search_input.setPlaceholderText("Suchen...")
        self.search_input.textChanged.connect(self.filter_workers)
        filter_layout.addWidget(self.search_input)
        
        # Abteilungs-Filter
        self.department_filter = QComboBox()
        self.department_filter.setObjectName("filter-select")
        self.department_filter.addItem("Alle Abteilungen")
        self.department_filter.currentTextChanged.connect(self.filter_workers)
        filter_layout.addWidget(self.department_filter)
        
        # Status Filter
        self.status_filter = QComboBox()
        self.status_filter.setObjectName("filter-select")
        self.status_filter.addItems(["Alle Status", "Aktiv", "Inaktiv"])
        self.status_filter.currentTextChanged.connect(self.filter_workers)
        filter_layout.addWidget(self.status_filter)
        
        # Neuer Mitarbeiter Button
        add_button = QPushButton("+ NEUER MITARBEITER")
        add_button.setObjectName("primary-button")
        add_button.clicked.connect(self.add_worker)
        filter_layout.addWidget(add_button)
        
        layout.addWidget(filter_container)
        
        # Tabelle
        self.table = QTableWidget()
        self.table.setObjectName("data-table")
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Name", "Barcode", "Abteilung", "Status",
            "Ausgeliehene Werkzeuge", "Aktionen"
        ])
        
        # Spaltenbreiten einstellen
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # Barcode
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Abteilung
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # Status
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)    # Ausgeliehen
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)    # Aktionen
        
        header.setFixedHeight(40)
        self.table.setColumnWidth(1, 120)  # Barcode
        self.table.setColumnWidth(2, 150)  # Abteilung
        self.table.setColumnWidth(3, 100)  # Status
        self.table.setColumnWidth(4, 150)  # Ausgeliehen
        self.table.setColumnWidth(5, 100)  # Aktionen
        
        layout.addWidget(self.table)
        
        # Beispieldaten laden
        self.load_data()
        
    def load_data(self):
        """Lädt die Mitarbeiterdaten"""
        # Beispieldaten
        workers = [
            {
                "name": "Max Mustermann",
                "barcode": "M001",
                "department": "Produktion",
                "status": "Aktiv",
                "tools": "2"
            },
            {
                "name": "Anna Schmidt",
                "barcode": "M002",
                "department": "Lager",
                "status": "Aktiv",
                "tools": "0"
            },
            {
                "name": "Peter Meyer",
                "barcode": "M003",
                "department": "Produktion",
                "status": "Inaktiv",
                "tools": "0"
            }
        ]
        
        # Tabelle leeren
        self.table.setRowCount(0)
        
        # Abteilungen sammeln
        departments = set()
        
        # Daten einfügen
        for worker in workers:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Name
            name_item = QTableWidgetItem(worker["name"])
            self.table.setItem(row, 0, name_item)
            
            # Barcode
            barcode_item = QTableWidgetItem(worker["barcode"])
            self.table.setItem(row, 1, barcode_item)
            
            # Abteilung
            department_item = QTableWidgetItem(worker["department"])
            self.table.setItem(row, 2, department_item)
            departments.add(worker["department"])
            
            # Status
            status_label = QLabel(worker["status"])
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if worker["status"] == "Aktiv":
                status_label.setObjectName("status-available")
            else:
                status_label.setObjectName("status-defect")
            self.table.setCellWidget(row, 3, status_label)
            
            # Ausgeliehene Werkzeuge
            tools_item = QTableWidgetItem(worker["tools"])
            tools_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, tools_item)
            
            # Aktionen
            action_container = QWidget()
            action_layout = QHBoxLayout(action_container)
            action_layout.setContentsMargins(4, 4, 4, 4)
            
            edit_button = QPushButton("📝")
            edit_button.clicked.connect(lambda _, w=worker: self.edit_worker(w))
            action_layout.addWidget(edit_button)
            
            delete_button = QPushButton("🗑")
            delete_button.clicked.connect(lambda _, w=worker: self.delete_worker(w))
            action_layout.addWidget(delete_button)
            
            self.table.setCellWidget(row, 5, action_container)
            
        # Filter aktualisieren
        self.department_filter.clear()
        self.department_filter.addItem("Alle Abteilungen")
        self.department_filter.addItems(sorted(departments))
        
    def filter_workers(self):
        """Filtert die Mitarbeiter nach den ausgewählten Kriterien"""
        search_text = self.search_input.text().lower()
        department = self.department_filter.currentText()
        status = self.status_filter.currentText()
        
        for row in range(self.table.rowCount()):
            show = True
            
            # Textsuche
            if search_text:
                name = self.table.item(row, 0).text().lower()
                barcode = self.table.item(row, 1).text().lower()
                if search_text not in name and search_text not in barcode:
                    show = False
            
            # Abteilungs-Filter
            if department != "Alle Abteilungen":
                if self.table.item(row, 2).text() != department:
                    show = False
                    
            # Status Filter
            if status != "Alle Status":
                status_label = self.table.cellWidget(row, 3)
                if status_label.text() != status:
                    show = False
                    
            self.table.setRowHidden(row, not show)
            
    def add_worker(self):
        """Öffnet den Dialog zum Hinzufügen eines Mitarbeiters"""
        print("Neuen Mitarbeiter hinzufügen")
        
    def edit_worker(self, worker):
        """Öffnet den Dialog zum Bearbeiten eines Mitarbeiters"""
        print(f"Mitarbeiter bearbeiten: {worker['name']}")
        
    def delete_worker(self, worker):
        """Löscht einen Mitarbeiter"""
        print(f"Mitarbeiter löschen: {worker['name']}") 
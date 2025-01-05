from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame,
    QHeaderView
)
from PyQt6.QtCore import Qt

class ToolsView(QWidget):
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
        self.search_input.textChanged.connect(self.filter_tools)
        filter_layout.addWidget(self.search_input)
        
        # Kategorie Filter
        self.category_filter = QComboBox()
        self.category_filter.setObjectName("filter-select")
        self.category_filter.addItem("Alle Kategorien")
        self.category_filter.currentTextChanged.connect(self.filter_tools)
        filter_layout.addWidget(self.category_filter)
        
        # Standort Filter
        self.location_filter = QComboBox()
        self.location_filter.setObjectName("filter-select")
        self.location_filter.addItem("Alle Standorte")
        self.location_filter.currentTextChanged.connect(self.filter_tools)
        filter_layout.addWidget(self.location_filter)
        
        # Status Filter
        self.status_filter = QComboBox()
        self.status_filter.setObjectName("filter-select")
        self.status_filter.addItems(["Alle Status", "Verfügbar", "Ausgeliehen", "Defekt"])
        self.status_filter.currentTextChanged.connect(self.filter_tools)
        filter_layout.addWidget(self.status_filter)
        
        # Neues Werkzeug Button
        add_button = QPushButton("+ NEUES WERKZEUG")
        add_button.setObjectName("primary-button")
        add_button.clicked.connect(self.add_tool)
        filter_layout.addWidget(add_button)
        
        layout.addWidget(filter_container)
        
        # Tabelle
        self.table = QTableWidget()
        self.table.setObjectName("data-table")
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Name", "Barcode", "Standort", "Status",
            "Kategorie", "Aktionen"
        ])
        
        # Spaltenbreiten einstellen
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # Barcode
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Standort
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # Status
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)    # Kategorie
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)    # Aktionen
        
        header.setFixedHeight(40)
        self.table.setColumnWidth(1, 120)  # Barcode
        self.table.setColumnWidth(2, 120)  # Standort
        self.table.setColumnWidth(3, 100)  # Status
        self.table.setColumnWidth(4, 120)  # Kategorie
        self.table.setColumnWidth(5, 100)  # Aktionen
        
        layout.addWidget(self.table)
        
        # Beispieldaten laden
        self.load_data()
        
    def load_data(self):
        """Lädt die Werkzeugdaten"""
        # Beispieldaten
        tools = [
            {
                "name": "Hammer",
                "barcode": "T001",
                "location": "Werkstatt",
                "status": "Verfügbar",
                "category": "Handwerkzeug"
            },
            {
                "name": "Bohrmaschine",
                "barcode": "T002",
                "location": "Lager",
                "status": "Ausgeliehen",
                "category": "Elektrowerkzeug"
            },
            {
                "name": "Schraubendreher",
                "barcode": "T003",
                "location": "Werkstatt",
                "status": "Defekt",
                "category": "Handwerkzeug"
            }
        ]
        
        # Tabelle leeren
        self.table.setRowCount(0)
        
        # Kategorien und Standorte sammeln
        categories = set()
        locations = set()
        
        # Daten einfügen
        for tool in tools:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Name
            name_item = QTableWidgetItem(tool["name"])
            self.table.setItem(row, 0, name_item)
            
            # Barcode
            barcode_item = QTableWidgetItem(tool["barcode"])
            self.table.setItem(row, 1, barcode_item)
            
            # Standort
            location_item = QTableWidgetItem(tool["location"])
            self.table.setItem(row, 2, location_item)
            locations.add(tool["location"])
            
            # Status
            status_label = QLabel(tool["status"])
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if tool["status"] == "Verfügbar":
                status_label.setObjectName("status-available")
            elif tool["status"] == "Ausgeliehen":
                status_label.setObjectName("status-lent")
            else:
                status_label.setObjectName("status-defect")
            self.table.setCellWidget(row, 3, status_label)
            
            # Kategorie
            category_item = QTableWidgetItem(tool["category"])
            self.table.setItem(row, 4, category_item)
            categories.add(tool["category"])
            
            # Aktionen
            action_container = QWidget()
            action_layout = QHBoxLayout(action_container)
            action_layout.setContentsMargins(4, 4, 4, 4)
            
            edit_button = QPushButton("📝")
            edit_button.clicked.connect(lambda _, t=tool: self.edit_tool(t))
            action_layout.addWidget(edit_button)
            
            delete_button = QPushButton("🗑")
            delete_button.clicked.connect(lambda _, t=tool: self.delete_tool(t))
            action_layout.addWidget(delete_button)
            
            self.table.setCellWidget(row, 5, action_container)
            
        # Filter aktualisieren
        self.category_filter.clear()
        self.category_filter.addItem("Alle Kategorien")
        self.category_filter.addItems(sorted(categories))
        
        self.location_filter.clear()
        self.location_filter.addItem("Alle Standorte")
        self.location_filter.addItems(sorted(locations))
        
    def filter_tools(self):
        """Filtert die Werkzeuge nach den ausgewählten Kriterien"""
        search_text = self.search_input.text().lower()
        category = self.category_filter.currentText()
        location = self.location_filter.currentText()
        status = self.status_filter.currentText()
        
        for row in range(self.table.rowCount()):
            show = True
            
            # Textsuche
            if search_text:
                name = self.table.item(row, 0).text().lower()
                barcode = self.table.item(row, 1).text().lower()
                if search_text not in name and search_text not in barcode:
                    show = False
            
            # Kategorie Filter
            if category != "Alle Kategorien":
                if self.table.item(row, 4).text() != category:
                    show = False
                    
            # Standort Filter
            if location != "Alle Standorte":
                if self.table.item(row, 2).text() != location:
                    show = False
                    
            # Status Filter
            if status != "Alle Status":
                status_label = self.table.cellWidget(row, 3)
                if status_label.text() != status:
                    show = False
                    
            self.table.setRowHidden(row, not show)
            
    def add_tool(self):
        """Öffnet den Dialog zum Hinzufügen eines Werkzeugs"""
        print("Neues Werkzeug hinzufügen")
        
    def edit_tool(self, tool):
        """Öffnet den Dialog zum Bearbeiten eines Werkzeugs"""
        print(f"Werkzeug bearbeiten: {tool['name']}")
        
    def delete_tool(self, tool):
        """Löscht ein Werkzeug"""
        print(f"Werkzeug löschen: {tool['name']}") 
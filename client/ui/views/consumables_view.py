from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame,
    QHeaderView
)
from PyQt6.QtCore import Qt

class ConsumablesView(QWidget):
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
        self.search_input.textChanged.connect(self.filter_consumables)
        filter_layout.addWidget(self.search_input)
        
        # Kategorie Filter
        self.category_filter = QComboBox()
        self.category_filter.setObjectName("filter-select")
        self.category_filter.addItem("Alle Kategorien")
        self.category_filter.currentTextChanged.connect(self.filter_consumables)
        filter_layout.addWidget(self.category_filter)
        
        # Standort Filter
        self.location_filter = QComboBox()
        self.location_filter.setObjectName("filter-select")
        self.location_filter.addItem("Alle Standorte")
        self.location_filter.currentTextChanged.connect(self.filter_consumables)
        filter_layout.addWidget(self.location_filter)
        
        # Status Filter
        self.status_filter = QComboBox()
        self.status_filter.setObjectName("filter-select")
        self.status_filter.addItems(["Alle Status", "Verfügbar", "Nachbestellen"])
        self.status_filter.currentTextChanged.connect(self.filter_consumables)
        filter_layout.addWidget(self.status_filter)
        
        # Neues Material Button
        add_button = QPushButton("+ NEUES MATERIAL")
        add_button.setObjectName("primary-button")
        add_button.clicked.connect(self.add_consumable)
        filter_layout.addWidget(add_button)
        
        layout.addWidget(filter_container)
        
        # Tabelle
        self.table = QTableWidget()
        self.table.setObjectName("data-table")
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Name", "Barcode", "Standort", "Kategorie",
            "Bestand", "Status", "Aktionen"
        ])
        
        # Spaltenbreiten einstellen
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # Barcode
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Standort
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # Kategorie
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)    # Bestand
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)    # Status
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)    # Aktionen
        
        header.setFixedHeight(40)
        self.table.setColumnWidth(1, 120)  # Barcode
        self.table.setColumnWidth(2, 120)  # Standort
        self.table.setColumnWidth(3, 120)  # Kategorie
        self.table.setColumnWidth(4, 100)  # Bestand
        self.table.setColumnWidth(5, 100)  # Status
        self.table.setColumnWidth(6, 100)  # Aktionen
        
        layout.addWidget(self.table)
        
        # Beispieldaten laden
        self.load_data()
        
    def load_data(self):
        """Lädt die Verbrauchsmaterialdaten"""
        # Beispieldaten
        consumables = [
            {
                "name": "Schrauben M4",
                "barcode": "C001",
                "location": "Lager",
                "category": "Schrauben",
                "quantity": "150",
                "min_quantity": "100",
                "status": "Verfügbar"
            },
            {
                "name": "Kabelverbinder",
                "barcode": "C002",
                "location": "Werkstatt",
                "category": "Elektro",
                "quantity": "20",
                "min_quantity": "50",
                "status": "Nachbestellen"
            },
            {
                "name": "Klebeband",
                "barcode": "C003",
                "location": "Lager",
                "category": "Verbrauch",
                "quantity": "45",
                "min_quantity": "30",
                "status": "Verfügbar"
            }
        ]
        
        # Tabelle leeren
        self.table.setRowCount(0)
        
        # Kategorien und Standorte sammeln
        categories = set()
        locations = set()
        
        # Daten einfügen
        for consumable in consumables:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Name
            name_item = QTableWidgetItem(consumable["name"])
            self.table.setItem(row, 0, name_item)
            
            # Barcode
            barcode_item = QTableWidgetItem(consumable["barcode"])
            self.table.setItem(row, 1, barcode_item)
            
            # Standort
            location_item = QTableWidgetItem(consumable["location"])
            self.table.setItem(row, 2, location_item)
            locations.add(consumable["location"])
            
            # Kategorie
            category_item = QTableWidgetItem(consumable["category"])
            self.table.setItem(row, 3, category_item)
            categories.add(consumable["category"])
            
            # Bestand
            quantity_item = QTableWidgetItem(consumable["quantity"])
            quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, quantity_item)
            
            # Status
            status_label = QLabel(consumable["status"])
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if consumable["status"] == "Verfügbar":
                status_label.setObjectName("status-available")
            else:
                status_label.setObjectName("status-defect")
            self.table.setCellWidget(row, 5, status_label)
            
            # Aktionen
            action_container = QWidget()
            action_layout = QHBoxLayout(action_container)
            action_layout.setContentsMargins(4, 4, 4, 4)
            
            edit_button = QPushButton("📝")
            edit_button.clicked.connect(lambda _, c=consumable: self.edit_consumable(c))
            action_layout.addWidget(edit_button)
            
            delete_button = QPushButton("🗑")
            delete_button.clicked.connect(lambda _, c=consumable: self.delete_consumable(c))
            action_layout.addWidget(delete_button)
            
            self.table.setCellWidget(row, 6, action_container)
            
        # Filter aktualisieren
        self.category_filter.clear()
        self.category_filter.addItem("Alle Kategorien")
        self.category_filter.addItems(sorted(categories))
        
        self.location_filter.clear()
        self.location_filter.addItem("Alle Standorte")
        self.location_filter.addItems(sorted(locations))
        
    def filter_consumables(self):
        """Filtert die Verbrauchsmaterialien nach den ausgewählten Kriterien"""
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
                if self.table.item(row, 3).text() != category:
                    show = False
                    
            # Standort Filter
            if location != "Alle Standorte":
                if self.table.item(row, 2).text() != location:
                    show = False
                    
            # Status Filter
            if status != "Alle Status":
                status_label = self.table.cellWidget(row, 5)
                if status_label.text() != status:
                    show = False
                    
            self.table.setRowHidden(row, not show)
            
    def add_consumable(self):
        """Öffnet den Dialog zum Hinzufügen eines Verbrauchsmaterials"""
        print("Neues Material hinzufügen")
        
    def edit_consumable(self, consumable):
        """Öffnet den Dialog zum Bearbeiten eines Verbrauchsmaterials"""
        print(f"Material bearbeiten: {consumable['name']}")
        
    def delete_consumable(self, consumable):
        """Löscht ein Verbrauchsmaterial"""
        print(f"Material löschen: {consumable['name']}") 
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QComboBox, QPushButton,
                               QMessageBox, QFormLayout)
from PyQt6.QtCore import Qt

class ToolDialog(QDialog):
    def __init__(self, client, parent=None, tool_data=None):
        super().__init__(parent)
        self.client = client
        self.tool_data = tool_data
        self.init_ui()
        
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        self.setWindowTitle("Werkzeug hinzufügen" if not self.tool_data else "Werkzeug bearbeiten")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Formular
        form = QFormLayout()
        
        # Barcode
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Barcode scannen oder eingeben")
        if self.tool_data:
            self.barcode_input.setText(self.tool_data.get('barcode', ''))
            self.barcode_input.setReadOnly(True)
        form.addRow("Barcode:", self.barcode_input)
        
        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Name des Werkzeugs")
        if self.tool_data:
            self.name_input.setText(self.tool_data.get('name', ''))
        form.addRow("Name:", self.name_input)
        
        # Beschreibung
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Beschreibung des Werkzeugs")
        if self.tool_data:
            self.description_input.setText(self.tool_data.get('description', ''))
        form.addRow("Beschreibung:", self.description_input)
        
        # Status
        self.status_input = QComboBox()
        self.status_input.addItems(['verfügbar', 'defekt'])
        if self.tool_data:
            current_status = self.tool_data.get('status', 'verfügbar')
            index = self.status_input.findText(current_status)
            if index >= 0:
                self.status_input.setCurrentIndex(index)
        form.addRow("Status:", self.status_input)
        
        # Kategorie
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
        if self.tool_data:
            self.category_input.setCurrentText(self.tool_data.get('category', ''))
        form.addRow("Kategorie:", self.category_input)
        
        # Standort
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Standort des Werkzeugs")
        if self.tool_data:
            self.location_input.setText(self.tool_data.get('location', ''))
        form.addRow("Standort:", self.location_input)
        
        layout.addLayout(form)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Abbrechen")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        save_button = QPushButton("Speichern")
        save_button.clicked.connect(self.save_tool)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Kategorien laden
        self.load_categories()
        
    def load_categories(self):
        """Lädt die vorhandenen Kategorien"""
        try:
            categories = self.client.get_tool_categories()
            self.category_input.clear()
            self.category_input.addItems(sorted(categories))
        except Exception as e:
            print(f"Fehler beim Laden der Kategorien: {str(e)}")
            
    def validate(self):
        """Validiert die Eingaben"""
        if not self.barcode_input.text():
            QMessageBox.warning(self, "Fehler", "Bitte einen Barcode eingeben")
            return False
            
        if not self.name_input.text():
            QMessageBox.warning(self, "Fehler", "Bitte einen Namen eingeben")
            return False
            
        return True
        
    def save_tool(self):
        """Speichert das Werkzeug"""
        if not self.validate():
            return
            
        tool_data = {
            'barcode': self.barcode_input.text(),
            'name': self.name_input.text(),
            'description': self.description_input.text(),
            'status': self.status_input.currentText(),
            'category': self.category_input.currentText(),
            'location': self.location_input.text()
        }
        
        try:
            if self.tool_data:
                success = self.client.update_tool(tool_data)
            else:
                success = self.client.create_tool(tool_data)
                
            if success:
                self.accept()
            else:
                QMessageBox.warning(self, "Fehler", "Werkzeug konnte nicht gespeichert werden")
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {str(e)}") 
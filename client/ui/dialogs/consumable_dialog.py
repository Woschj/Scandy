from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QComboBox, QPushButton,
                               QMessageBox, QFormLayout, QSpinBox)
from PyQt6.QtCore import Qt

class ConsumableDialog(QDialog):
    def __init__(self, client, parent=None, consumable_data=None):
        super().__init__(parent)
        self.client = client
        self.consumable_data = consumable_data
        self.init_ui()
        
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        self.setWindowTitle("Verbrauchsmaterial hinzufügen" if not self.consumable_data else "Verbrauchsmaterial bearbeiten")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Formular
        form = QFormLayout()
        
        # Barcode
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Barcode scannen oder eingeben")
        if self.consumable_data:
            self.barcode_input.setText(self.consumable_data.get('barcode', ''))
            self.barcode_input.setReadOnly(True)
        form.addRow("Barcode:", self.barcode_input)
        
        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Name des Materials")
        if self.consumable_data:
            self.name_input.setText(self.consumable_data.get('name', ''))
        form.addRow("Name:", self.name_input)
        
        # Beschreibung
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Beschreibung des Materials")
        if self.consumable_data:
            self.description_input.setText(self.consumable_data.get('description', ''))
        form.addRow("Beschreibung:", self.description_input)
        
        # Menge
        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(0)
        self.quantity_input.setMaximum(999999)
        if self.consumable_data:
            self.quantity_input.setValue(self.consumable_data.get('quantity', 0))
        form.addRow("Menge:", self.quantity_input)
        
        # Mindestmenge
        self.min_quantity_input = QSpinBox()
        self.min_quantity_input.setMinimum(0)
        self.min_quantity_input.setMaximum(999999)
        if self.consumable_data:
            self.min_quantity_input.setValue(self.consumable_data.get('min_quantity', 0))
        form.addRow("Mindestmenge:", self.min_quantity_input)
        
        # Kategorie
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
        if self.consumable_data:
            self.category_input.setCurrentText(self.consumable_data.get('category', ''))
        form.addRow("Kategorie:", self.category_input)
        
        # Standort
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Standort des Materials")
        if self.consumable_data:
            self.location_input.setText(self.consumable_data.get('location', ''))
        form.addRow("Standort:", self.location_input)
        
        layout.addLayout(form)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Abbrechen")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        save_button = QPushButton("Speichern")
        save_button.clicked.connect(self.save_consumable)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Kategorien laden
        self.load_categories()
        
    def load_categories(self):
        """Lädt die vorhandenen Kategorien"""
        try:
            categories = self.client.get_consumable_categories()
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
            
        if self.min_quantity_input.value() > self.quantity_input.value():
            QMessageBox.warning(self, "Fehler", "Mindestmenge kann nicht größer als aktuelle Menge sein")
            return False
            
        return True
        
    def save_consumable(self):
        """Speichert das Verbrauchsmaterial"""
        if not self.validate():
            return
            
        consumable_data = {
            'barcode': self.barcode_input.text(),
            'name': self.name_input.text(),
            'description': self.description_input.text(),
            'quantity': self.quantity_input.value(),
            'min_quantity': self.min_quantity_input.value(),
            'category': self.category_input.currentText(),
            'location': self.location_input.text()
        }
        
        try:
            if self.consumable_data:
                success = self.client.update_consumable(consumable_data)
            else:
                success = self.client.create_consumable(consumable_data)
                
            if success:
                self.accept()
            else:
                QMessageBox.warning(self, "Fehler", "Verbrauchsmaterial konnte nicht gespeichert werden")
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {str(e)}") 
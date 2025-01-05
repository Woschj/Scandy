from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QComboBox, QPushButton,
                               QMessageBox, QFormLayout)
from PyQt6.QtCore import Qt

class WorkerDialog(QDialog):
    def __init__(self, client, parent=None, worker_data=None):
        super().__init__(parent)
        self.client = client
        self.worker_data = worker_data
        self.init_ui()
        
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        self.setWindowTitle("Mitarbeiter hinzufügen" if not self.worker_data else "Mitarbeiter bearbeiten")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Formular
        form = QFormLayout()
        
        # Barcode
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Barcode scannen oder eingeben")
        if self.worker_data:
            self.barcode_input.setText(self.worker_data.get('barcode', ''))
            self.barcode_input.setReadOnly(True)
        form.addRow("Barcode:", self.barcode_input)
        
        # Vorname
        self.firstname_input = QLineEdit()
        self.firstname_input.setPlaceholderText("Vorname des Mitarbeiters")
        if self.worker_data:
            self.firstname_input.setText(self.worker_data.get('firstname', ''))
        form.addRow("Vorname:", self.firstname_input)
        
        # Nachname
        self.lastname_input = QLineEdit()
        self.lastname_input.setPlaceholderText("Nachname des Mitarbeiters")
        if self.worker_data:
            self.lastname_input.setText(self.worker_data.get('lastname', ''))
        form.addRow("Nachname:", self.lastname_input)
        
        # Abteilung
        self.department_input = QComboBox()
        self.department_input.setEditable(True)
        self.department_input.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
        if self.worker_data:
            self.department_input.setCurrentText(self.worker_data.get('department', ''))
        form.addRow("Abteilung:", self.department_input)
        
        # E-Mail
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("E-Mail-Adresse")
        if self.worker_data:
            self.email_input.setText(self.worker_data.get('email', ''))
        form.addRow("E-Mail:", self.email_input)
        
        layout.addLayout(form)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Abbrechen")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        save_button = QPushButton("Speichern")
        save_button.clicked.connect(self.save_worker)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Abteilungen laden
        self.load_departments()
        
    def load_departments(self):
        """Lädt die vorhandenen Abteilungen"""
        try:
            departments = self.client.get_departments()
            self.department_input.clear()
            self.department_input.addItems(sorted(departments))
        except Exception as e:
            print(f"Fehler beim Laden der Abteilungen: {str(e)}")
            
    def validate(self):
        """Validiert die Eingaben"""
        if not self.barcode_input.text():
            QMessageBox.warning(self, "Fehler", "Bitte einen Barcode eingeben")
            return False
            
        if not self.firstname_input.text():
            QMessageBox.warning(self, "Fehler", "Bitte einen Vornamen eingeben")
            return False
            
        if not self.lastname_input.text():
            QMessageBox.warning(self, "Fehler", "Bitte einen Nachnamen eingeben")
            return False
            
        return True
        
    def save_worker(self):
        """Speichert den Mitarbeiter"""
        if not self.validate():
            return
            
        worker_data = {
            'barcode': self.barcode_input.text(),
            'firstname': self.firstname_input.text(),
            'lastname': self.lastname_input.text(),
            'department': self.department_input.currentText(),
            'email': self.email_input.text()
        }
        
        try:
            if self.worker_data:
                success = self.client.update_worker(worker_data)
            else:
                success = self.client.create_worker(worker_data)
                
            if success:
                self.accept()
            else:
                QMessageBox.warning(self, "Fehler", "Mitarbeiter konnte nicht gespeichert werden")
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {str(e)}") 
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QPushButton, QFrame,
                               QMessageBox)
from PyQt6.QtCore import Qt

class SetupView(QWidget):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.init_ui()
        
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Container für das Setup-Formular
        container = QFrame()
        container.setObjectName("setup-container")
        container.setMinimumWidth(400)
        container.setMaximumWidth(600)
        
        container_layout = QVBoxLayout()
        
        # Überschrift
        header = QLabel("Ersteinrichtung")
        header.setObjectName("setup-header")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(header)
        
        # Formular
        form_layout = QVBoxLayout()
        
        # Benutzername
        username_label = QLabel("Benutzername")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Benutzername eingeben")
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_input)
        
        # Passwort
        password_label = QLabel("Passwort")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Passwort eingeben")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        
        # Passwort wiederholen
        password2_label = QLabel("Passwort wiederholen")
        self.password2_input = QLineEdit()
        self.password2_input.setPlaceholderText("Passwort wiederholen")
        self.password2_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(password2_label)
        form_layout.addWidget(self.password2_input)
        
        # Submit Button
        submit_button = QPushButton("Administrator-Account erstellen")
        submit_button.setObjectName("submit-button")
        submit_button.clicked.connect(self.handle_submit)
        
        # Alles zum Container hinzufügen
        container_layout.addLayout(form_layout)
        container_layout.addWidget(submit_button)
        container.setLayout(container_layout)
        
        # Container zum Hauptlayout hinzufügen
        layout.addWidget(container)
        self.setLayout(layout)
        
    def handle_submit(self):
        """Verarbeitet das Absenden des Formulars"""
        username = self.username_input.text()
        password = self.password_input.text()
        password2 = self.password2_input.text()
        
        # Validierung
        if not username:
            QMessageBox.warning(self, "Fehler", "Bitte einen Benutzernamen eingeben")
            return
            
        if not password:
            QMessageBox.warning(self, "Fehler", "Bitte ein Passwort eingeben")
            return
            
        if password != password2:
            QMessageBox.warning(self, "Fehler", "Passwörter stimmen nicht überein")
            return
            
        if len(password) < 8:
            QMessageBox.warning(self, "Fehler", "Passwort muss mindestens 8 Zeichen lang sein")
            return
            
        # Setup durchführen
        try:
            if self.client.setup(username, password):
                QMessageBox.information(self, "Erfolg", "Setup erfolgreich abgeschlossen")
                # Zum Login wechseln
                self.parent().parent().show_login()
            else:
                QMessageBox.warning(self, "Fehler", "Setup konnte nicht durchgeführt werden")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Setup: {str(e)}") 
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

class LoginView(QWidget):
    login_successful = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Login Container
        container = QFrame()
        container.setObjectName("login-container")
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Login Box
        login_box = QFrame()
        login_box.setObjectName("login-box")
        login_box.setFixedWidth(400)
        box_layout = QVBoxLayout(login_box)
        box_layout.setSpacing(20)
        
        # Header
        header = QLabel("Anmeldung")
        header.setObjectName("login-header")
        box_layout.addWidget(header)
        
        # Benutzername
        username_label = QLabel("Benutzername")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Benutzername eingeben")
        box_layout.addWidget(username_label)
        box_layout.addWidget(self.username_input)
        
        # Passwort
        password_label = QLabel("Passwort")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Passwort eingeben")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        box_layout.addWidget(password_label)
        box_layout.addWidget(self.password_input)
        
        # Fehlermeldung
        self.error_label = QLabel()
        self.error_label.setObjectName("error-message")
        self.error_label.hide()
        box_layout.addWidget(self.error_label)
        
        # Login Button
        button_container = QHBoxLayout()
        button_container.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        login_button = QPushButton("Anmelden")
        login_button.setObjectName("primary-button")
        login_button.clicked.connect(self.handle_login)
        button_container.addWidget(login_button)
        
        box_layout.addLayout(button_container)
        
        container_layout.addWidget(login_box)
        layout.addWidget(container)
        
    def handle_login(self):
        """Behandelt den Login-Versuch"""
        username = self.username_input.text()
        password = self.password_input.text()
        
        if username == "admin" and password == "admin":  # Nur für Demo
            self.login_successful.emit()
            self.clear_inputs()
            self.error_label.hide()
        else:
            self.error_label.setText("Ungültige Anmeldedaten")
            self.error_label.show()
            
    def clear_inputs(self):
        """Leert die Eingabefelder"""
        self.username_input.clear()
        self.password_input.clear() 
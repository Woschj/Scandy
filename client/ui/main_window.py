from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QFont

from .views.index_view import IndexView
from .views.tools_view import ToolsView
from .views.workers_view import WorkersView
from .views.consumables_view import ConsumablesView
from .views.scan_view import ScanView
from .views.login_view import LoginView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scandy")
        self.setMinimumSize(1200, 800)
        
        # Zentrales Widget erstellen
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Hauptlayout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Linke Navigationsleiste
        self.left_nav = self.create_left_nav()
        main_layout.addWidget(self.left_nav)
        
        # Content-Bereich
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Obere Navigationsleiste
        self.top_nav = self.create_top_nav()
        content_layout.addWidget(self.top_nav)
        
        # Gestapelte Ansichten
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)
        
        # Ansichten hinzufügen
        self.index_view = IndexView()
        self.tools_view = ToolsView()
        self.workers_view = WorkersView()
        self.consumables_view = ConsumablesView()
        self.scan_view = ScanView()
        self.login_view = LoginView()
        
        self.stacked_widget.addWidget(self.index_view)
        self.stacked_widget.addWidget(self.tools_view)
        self.stacked_widget.addWidget(self.workers_view)
        self.stacked_widget.addWidget(self.consumables_view)
        self.stacked_widget.addWidget(self.scan_view)
        self.stacked_widget.addWidget(self.login_view)
        
        main_layout.addWidget(content_container)
        
        # Standardansicht setzen
        self.stacked_widget.setCurrentWidget(self.index_view)
        
    def create_left_nav(self):
        """Erstellt die linke Navigationsleiste"""
        nav_frame = QFrame()
        nav_frame.setObjectName("left-nav")
        
        layout = QVBoxLayout(nav_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Logo Container
        logo_container = QFrame()
        logo_container.setObjectName("nav-logo")
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        
        # Logo
        logo = QLabel()
        logo.setPixmap(QPixmap("client/ui/assets/scandy-logo.svg").scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo)
        
        layout.addWidget(logo_container)
        
        # Trennlinie
        separator = QFrame()
        separator.setObjectName("nav-separator")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        # Navigation Buttons
        nav_items = [
            ("scan", "Scannen", "🔍", self.show_scan_view),  # search
            ("tools", "Werkzeuge", "🔧", self.show_tools_view),  # tools
            ("workers", "Mitarbeiter", "👥", self.show_workers_view),  # users
            ("consumables", "Material", "📦", self.show_consumables_view)  # box
        ]
        
        for item_id, text, icon, callback in nav_items:
            btn = QPushButton(icon)
            btn.setObjectName(f"nav-{item_id}")
            btn.setCheckable(True)
            btn.setToolTip(text)  # Text als Tooltip anzeigen
            btn.clicked.connect(callback)
            layout.addWidget(btn)
            
        layout.addStretch()
        return nav_frame
        
    def create_top_nav(self):
        """Erstellt die obere Navigationsleiste"""
        nav_frame = QFrame()
        nav_frame.setObjectName("top-nav")
        
        layout = QHBoxLayout(nav_frame)
        layout.setContentsMargins(16, 0, 16, 0)
        
        # Seitentitel
        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("page-title")
        layout.addWidget(self.page_title)
        
        # BTZ Logo
        btz_logo = QLabel()
        btz_logo.setPixmap(QPixmap("client/ui/assets/BTZ_logo.jpg").scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        btz_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(btz_logo, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Rechte Navigation
        right_nav = QFrame()
        right_nav_layout = QHBoxLayout(right_nav)
        right_nav_layout.setSpacing(16)
        
        nav_items = [
            ("manual", "MANUELLE AUSLEIHE", "✋", self.show_scan_view),  # hand
            ("dashboard", "DASHBOARD", "📊", self.show_index_view),  # chart
            ("about", "ÜBER SCANDY", "ℹ️", self.show_about_view)  # info
        ]
        
        for item_id, text, icon, callback in nav_items:
            btn = QPushButton(icon + " " + text)
            btn.setObjectName(f"nav-{item_id}")
            btn.clicked.connect(callback)
            right_nav_layout.addWidget(btn)
            
        layout.addWidget(right_nav, alignment=Qt.AlignmentFlag.AlignRight)
        
        return nav_frame
        
    def show_index_view(self):
        self.stacked_widget.setCurrentWidget(self.index_view)
        self.page_title.setText("Dashboard")
        
    def show_tools_view(self):
        self.stacked_widget.setCurrentWidget(self.tools_view)
        self.page_title.setText("Werkzeuge")
        
    def show_workers_view(self):
        self.stacked_widget.setCurrentWidget(self.workers_view)
        self.page_title.setText("Mitarbeiter")
        
    def show_consumables_view(self):
        self.stacked_widget.setCurrentWidget(self.consumables_view)
        self.page_title.setText("Verbrauchsmaterial")
        
    def show_scan_view(self):
        self.stacked_widget.setCurrentWidget(self.scan_view)
        self.page_title.setText("Scannen")
        
    def show_about_view(self):
        # TODO: About-View implementieren
        pass 
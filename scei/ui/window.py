
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QDialog
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QSettings

from ..utils import apply_light_theme
from ..logger import add_log
from .. import session
from .widgets import TopBar, Sidebar
from .dialogs import LoginDialog
from ..data.repositories import add_bitacora_log, get_user
from .tabs.home import HomeTab
from .tabs.analitica import AnaliticaTab
from .tabs.bitacora import BitacoraTab
from .tabs.config import ConfigTab
from .tabs.container import ModulosTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")  # Permite styling específico en CSS
        self.setWindowTitle("SCEI - Sistema de Control de Equipos Informáticos")
        
        self.settings = QSettings("SCEI", "App")
        
        # Actions
        self.act_tema = QAction("Tema oscuro", self)
        self.act_tema.setCheckable(True)
        self.act_tema.triggered.connect(self.toggle_theme)

        # UI Logic
        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        self.topbar = TopBar()
        central_layout.addWidget(self.topbar)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = Sidebar()
        body_layout.addWidget(self.sidebar)

        self.main_stack = QStackedWidget()
        
        # Tabs
        self.home_tab = HomeTab()
        self.analitica_tab = AnaliticaTab()
        self.bitacora_tab = BitacoraTab()
        self.config_tab = ConfigTab()
        
        self.main_stack.addWidget(self.home_tab)      # 0
        self.main_stack.addWidget(self.analitica_tab) # 1
        self.main_stack.addWidget(self.bitacora_tab)  # 2
        self.main_stack.addWidget(self.config_tab)    # 3
        
        # ModulosTab (Detail) is dynamic, added when needed or managed here?
        # Better to add it dynamically or keep one instance if only one view active
        # We will add a placeholder or handle dynamic addition
        
        body_layout.addWidget(self.main_stack, 1)
        central_layout.addWidget(body, 1)
        self.setCentralWidget(central)
        self.statusBar()

        # Restore State (solo estado interno, sin geometría para evitar warnings de Qt)
        if (state := self.settings.value("main_state")):
            self.restoreState(state)

        # Connects
        self.sidebar.navigation_requested.connect(self.on_navigation)
        self.sidebar.btn_logout.clicked.connect(self.on_logout)
        
        self.home_tab.open_direccion.connect(self.open_modules)
        self.analitica_tab.open_direccion.connect(self.open_modules)

        # Init
        self.sidebar.select("direcciones")
        self.on_navigation("direcciones")

    def toggle_theme(self):
        dark = self.act_tema.isChecked()
        if dark:
            self.setStyleSheet("""
                QMainWindow, QWidget { background-color: #2b2b2b; color: #e0e0e0; }
                QLineEdit, QComboBox, QDateEdit { background-color: #3a3a3a; color: #e0e0e0; border: 1px solid #555; }
                QTableWidget { background-color: #333; gridline-color: #555; }
                QHeaderView::section { background-color: #444; color: #ddd; }
                QPushButton { background-color: #444; color: #e0e0e0; border: 1px solid #666; padding: 4px; }
                
                /* Fix Popups/Menus being white */
                QMenu { background-color: #2b2b2b; color: #e0e0e0; border: 1px solid #555; }
                QMenu::item { padding: 4px 20px; }
                QMenu::item:selected { background-color: #444; }
                
                QListView, QComboBox QAbstractItemView {
                    background-color: #3a3a3a; 
                    color: #e0e0e0;
                    selection-background-color: #555;
                    border: 1px solid #555;
                    outline: none;
                }
                QListView::item:selected { background-color: #555; }
                
                QToolTip { 
                    background-color: #333; 
                    color: #fff; 
                    border: 1px solid #555; 
                }
            """)
        else:
            apply_light_theme(self.sender().parent() if self.sender() else self) # hacky

    def on_navigation(self, key: str):
        self.sidebar.select(key)
        
        # If we are in Modulos (index > 3), remove it?
        while self.main_stack.count() > 4:
            w = self.main_stack.widget(4)
            self.main_stack.removeWidget(w)
            w.deleteLater()
            
        if key == "direcciones":
            self.main_stack.setCurrentWidget(self.home_tab)
            self.topbar.set_title("Direcciones")
        elif key == "analitica":
            self.main_stack.setCurrentWidget(self.analitica_tab)
            self.topbar.set_title("Analítica")
            self.analitica_tab.refresh()
        elif key == "bitacora":
            self.main_stack.setCurrentWidget(self.bitacora_tab)
            self.topbar.set_title("Bitácora")
            self.bitacora_tab.refresh()
        elif key == "configuracion":
            self.main_stack.setCurrentWidget(self.config_tab)
            self.topbar.set_title("Configuración")
            # Refrescar siempre los datos de perfil según el usuario actual
            self.config_tab.refresh()

    def open_modules(self, direccion_id: int):
        # Create new modules tab
        # Remove old if any (dynamic tabs start at index 4)
        while self.main_stack.count() > 4:
            w = self.main_stack.widget(4)
            self.main_stack.removeWidget(w)
            w.deleteLater()
            
        mod_tab = ModulosTab(direccion_id)
        mod_tab.back_requested.connect(lambda: self.on_navigation("direcciones"))
        self.main_stack.addWidget(mod_tab)
        self.main_stack.setCurrentWidget(mod_tab)
        
        self.sidebar.clear_selection()
        self.topbar.set_title("Módulos")

    def on_logout(self):
        if session.CURRENT_USER:
            add_log("Cierre de sesión", f"Usuario: {session.CURRENT_USER}")
            u_obj = get_user(session.CURRENT_USER)
            if u_obj:
                add_bitacora_log(u_obj.id, "Cierre de sesión", "Cierre de sesión manual", "Sistema")
        self.hide()
        login = LoginDialog()
        if login.exec() == QDialog.DialogCode.Accepted:
            self.showMaximized()
            self.sidebar.select("direcciones")
            self.on_navigation("direcciones")
        else:
            self.close()

    def closeEvent(self, e):
        self.settings.setValue("main_state", self.saveState())
        super().closeEvent(e)

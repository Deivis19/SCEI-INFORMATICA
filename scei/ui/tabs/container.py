
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QPushButton, QButtonGroup, QToolButton, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize

from ...utils import load_icon
from .equipos import EquiposTab
from .mantenimientos import MantenimientoTab

class ModulosTab(QWidget):
    # Señal para pedir volver atrás (cerrar este módulo y volver a home)
    back_requested = pyqtSignal()

    def __init__(self, direccion_id: int):
        super().__init__()
        self.direccion_id = direccion_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barra de navegación interna (Tabs superiores)
        # Contenedor para dar márgenes a la barra flotante
        nav_container = QWidget()
        nav_layout_outer = QVBoxLayout(nav_container)
        nav_layout_outer.setContentsMargins(24, 24, 24, 0) # Margen superior y lateral
        
        nav_bar = QWidget()
        nav_bar.setObjectName("ModuleNavBar")
        nav_bar.setProperty("class", "card") # Convertir en tarjeta flotante
        
        nav_h = QHBoxLayout(nav_bar)
        nav_h.setContentsMargins(20, 10, 20, 10)
        nav_h.setSpacing(16)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.btn_equipos = QToolButton()
        self.btn_equipos.setText("Equipos")
        self.btn_equipos.setIcon(load_icon("equipos.svg"))
        self.btn_equipos.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.btn_equipos.setIconSize(QSize(20, 20))
        self.btn_equipos.setCheckable(True)
        self.btn_equipos.setChecked(True)
        self.btn_equipos.setProperty("class", "module-nav-btn")
        self.btn_equipos.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_equipos.clicked.connect(lambda: self.on_nav_clicked(0))
        
        self.btn_mantenimientos = QToolButton()
        self.btn_mantenimientos.setText("Mantenimientos")
        self.btn_mantenimientos.setIcon(load_icon("maintenance.svg"))
        self.btn_mantenimientos.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.btn_mantenimientos.setIconSize(QSize(20, 20))
        self.btn_mantenimientos.setCheckable(True)
        self.btn_mantenimientos.setProperty("class", "module-nav-btn")
        self.btn_mantenimientos.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mantenimientos.clicked.connect(lambda: self.on_nav_clicked(1))

        self.nav_group.addButton(self.btn_equipos)
        self.nav_group.addButton(self.btn_mantenimientos)

        nav_h.addWidget(self.btn_equipos)
        nav_h.addWidget(self.btn_mantenimientos)
        # nav_h.addStretch(1) # Removed internal stretch so bar fits content

        # Center the navbar and let it shrink to content
        h_center = QHBoxLayout()
        h_center.addStretch(1)
        h_center.addWidget(nav_bar)
        h_center.addStretch(1)

        nav_layout_outer.addLayout(h_center)
        layout.addWidget(nav_container)

        # ScrollArea para contenido del módulo (evitar recorte en pantallas pequeñas)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        # Stack de contenido
        self.stack = QStackedWidget()
        self.equipos_tab = EquiposTab(direccion_id=direccion_id)
        self.mantenimientos_tab = MantenimientoTab(direccion_id=direccion_id)
        
        self.stack.addWidget(self.equipos_tab)
        self.stack.addWidget(self.mantenimientos_tab)
        
        scroll.setWidget(self.stack)
        layout.addWidget(scroll)

    def on_nav_clicked(self, index):
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.btn_equipos.setChecked(True)
        else:
            self.btn_mantenimientos.setChecked(True)

    def refresh(self):
        self.equipos_tab.refresh()
        self.mantenimientos_tab.refresh()

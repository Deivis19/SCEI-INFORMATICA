
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QLineEdit, QMessageBox, QToolTip, QDialog,
    QScrollArea, QGridLayout, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor

from ..dialogs import DireccionDialog, AdminAuthDialog
from ...logger import add_log
from ... import session
from ...config import DIRECCIONES_HIERARCHY
from ...data.repositories import (
    list_direcciones, add_direccion, update_direccion, delete_direccion,
    add_bitacora_log, get_user
)
from ...utils import load_icon

class HomeTab(QWidget):
    open_direccion = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 24)
        main_layout.setSpacing(20)

        # Header unified (Title --- Search + Button)
        header_row = QHBoxLayout()
        header_row.setSpacing(12) # Gap between search and button
        
        lbl_title = QLabel("Direcciones")
        lbl_title.setStyleSheet("font-size: 24px; font-weight: 700; color: #F8FAFC;")
        header_row.addWidget(lbl_title)
        
        header_row.addStretch(1)
        
        # Buscador
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar dirección...")
        self.search.setFixedWidth(350) # Encogido y fijo
        self.search.setStyleSheet("""
            QLineEdit {
                border-radius: 20px;
                padding: 10px 20px;
                background: rgba(30, 41, 59, 0.6);
                border: 1px solid rgba(148, 163, 184, 0.2);
                color: #F1F5F9;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #38BDF8;
                background: rgba(30, 41, 59, 0.9);
            }
        """)
        self.search.textChanged.connect(self.refresh)
        header_row.addWidget(self.search)
        
        # Boton Nuevo
        btn_new = QPushButton("Nueva") # Texto mas corto opcional
        btn_new.setProperty("class", "primary")
        btn_new.setMinimumHeight(40)
        btn_new.setIcon(load_icon("plus.svg")) 
        btn_new.clicked.connect(self.on_add)
        header_row.addWidget(btn_new)
        
        main_layout.addLayout(header_row)

        # Scroll Area para las tarjetas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(0, 0, 0, 40)
        # Alineación arriba-izquierda
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        scroll.setWidget(self.container)
        main_layout.addWidget(scroll)

        self.refresh()

    def refresh(self):
        # Limpiar grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        term = self.search.text().strip().lower()
        data = list_direcciones()
        
        # Filtrar
        filtered = [d for d in data if not term or term in (d.nombre or "").lower()]
        
        # Ordenar (Jerarquía hardcoded en config)
        pos_map = {name: i for i, name in enumerate(DIRECCIONES_HIERARCHY)}
        filtered.sort(key=lambda d: (pos_map.get(d.nombre or "", 10000), (d.nombre or "").lower()))

        # Renderizar tarjetas
        row = 0
        col = 0
        max_cols = 3 # 3 columnas para pantallas medianas/grandes
        
        for i, d in enumerate(filtered, 1):
            card = self.create_card(d, i)
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def create_card(self, direccion, index):
        card = QWidget()
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setObjectName("DireccionCard")
        # Estilo inline para hover effects customizados si se quisiera, 
        # pero usaremos clases de QSS mayormente.
        # Aquí forzamos un estilo específico de tarjeta "boton"
        card.setStyleSheet("""
            QWidget#DireccionCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(30, 41, 59, 0.7), stop:1 rgba(15, 23, 42, 0.8));
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 16px;
            }
            QWidget#DireccionCard:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(56, 189, 248, 0.15), stop:1 rgba(15, 23, 42, 0.9));
                border: 1px solid rgba(56, 189, 248, 0.5);
            }
        """)
        
        # Evento click manual
        card.mouseReleaseEvent = lambda e: self.open_direccion.emit(direccion.id)

        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(20, 24, 20, 24)
        vbox.setSpacing(12)

        # Numero secuencial
        icon_lbl = QLabel(str(index))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setFixedSize(48, 48)
        icon_lbl.setStyleSheet("""
            background: rgba(56, 189, 248, 0.1);
            color: #38BDF8;
            font-size: 20px;
            font-weight: 700;
            border-radius: 24px;
            border: 1px solid rgba(56, 189, 248, 0.3);
        """)
        
        name_lbl = QLabel(direccion.nombre)
        name_lbl.setWordWrap(True)
        name_lbl.setStyleSheet("font-size: 16px; font-weight: 600; color: #F1F5F9;")
        
        # Botón de menú (dots)
        btn_menu = QPushButton()
        btn_menu.setText("⋮")
        btn_menu.setFixedSize(30, 30)
        btn_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_menu.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94A3B8;
                font-size: 20px;
                font-weight: 900;
                border: none;
                border-radius: 15px;
            }
            QPushButton:hover {
                background: rgba(148, 163, 184, 0.1);
                color: #F8FAFC;
            }
        """)
        
        # Conexión para abrir menú
        def show_menu():
            menu = QMenu(card)
            # El estilo ya está en el QSS global (light.qss)
            
            act_edit = menu.addAction(load_icon("edit.svg"), "Editar")
            act_del = menu.addAction(load_icon("trash.svg"), "Eliminar")
            
            # Ejecutar menú en la posición del mouse
            action = menu.exec(QCursor.pos())
            
            if action == act_edit:
                self.on_update_card(direccion.id)
            elif action == act_del:
                self.on_delete_card(direccion.id)

        btn_menu.clicked.connect(show_menu)
        
        
        # Layout superior de la tarjeta para poner el menú a la derecha
        top_row = QHBoxLayout()
        top_row.addWidget(icon_lbl)
        top_row.addStretch(1)
        top_row.addWidget(btn_menu)
        
        vbox.addLayout(top_row)
        
        vbox.addWidget(name_lbl)
        
        return card

    def on_add(self):
        # Restriction: Only Admin or Authed
        if session.CURRENT_USER != "DI-ADMIN":
             auth = AdminAuthDialog(self, "Se requieren permisos de administrador para crear nuevas direcciones.")
             if auth.exec() != QDialog.DialogCode.Accepted:
                 return

        dlg = DireccionDialog()
        if dlg.exec() == QDialog.DialogCode.Accepted:
            nombre = dlg.values()
            if nombre:
                add_direccion(nombre)
                add_log("Dirección creada", f"Nombre: {nombre}")
                
                # Bitacora
                try:
                    u_obj = get_user(session.CURRENT_USER)
                    if u_obj:
                        add_bitacora_log(u_obj.id, "Crear Dirección", f"Creó la dirección: {nombre}", "Direcciones")
                except: pass
                
                self.refresh()

    def on_update_card(self, d_id):
        # Restriction: Only Admin or Authed
        if session.CURRENT_USER != "DI-ADMIN":
             auth = AdminAuthDialog(self, "Se requieren permisos de administrador para editar direcciones.")
             if auth.exec() != QDialog.DialogCode.Accepted:
                 return

        # hack para evitar que el click se propague a la tarjeta
        # (aunque en Qt el boton captura el click primero usualmente)
        data = list_direcciones()
        direc = next((d for d in data if d.id == d_id), None)
        if not direc: return
        
        old_name = direc.nombre
        dlg = DireccionDialog(direc.nombre)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_name = dlg.values()
            if new_name:
                update_direccion(d_id, new_name, 1) # Activo por defecto 1 al editar nombre
                add_log("Dirección actualizada", f"ID: {d_id} -> {new_name}")
                
                # Bitacora
                try:
                    u_obj = get_user(session.CURRENT_USER)
                    if u_obj:
                        add_bitacora_log(u_obj.id, "Editar Dirección", f"Editó dirección: {old_name} -> {new_name}", "Direcciones")
                except: pass
                
                self.refresh()

    def on_delete_card(self, d_id):
        # Restriction: Only Admin or Authed
        if session.CURRENT_USER != "DI-ADMIN":
             auth = AdminAuthDialog(self, "Se requieren permisos de administrador para eliminar direcciones.")
             if auth.exec() != QDialog.DialogCode.Accepted:
                 return

        data = list_direcciones()
        direc = next((d for d in data if d.id == d_id), None)
        dir_name = direc.nombre if direc else str(d_id)

        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            "¿Estás seguro de eliminar esta dirección?\nSe eliminarán sus equipos y mantenimientos asociados.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_direccion(d_id)
            add_log("Dirección eliminada", f"ID: {d_id}")
            
            # Bitacora
            try:
                u_obj = get_user(session.CURRENT_USER)
                if u_obj:
                    add_bitacora_log(u_obj.id, "Eliminar Dirección", f"Eliminó la dirección: {dir_name}", "Direcciones")
            except: pass
            
            self.refresh()


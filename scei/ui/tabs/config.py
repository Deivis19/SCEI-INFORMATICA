
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QMessageBox, QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt
from ... import session
from ...utils import load_icon, validate_password_strength
from ...data.repositories import get_user, update_user_profile, delete_user, list_users_full, add_bitacora_log
from ..dialogs import AdminAuthDialog, UserEditDialog
from ..biometrics import FaceCaptureDialog

class ConfigTab(QWidget):
    def __init__(self):
        super().__init__()
        
        # Main Layout (holds ScrollArea)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        # Main Horizontal Layout for Cards
        self.cards_container = QWidget()
        
        # APPLY PREMIUM STYLESHEET TO THE SCROLL AREA CONTENT
        self.cards_container.setStyleSheet("""
            QWidget {
                background: transparent;
                color: #e0e0e0;
            }
            QWidget[class="card"] {
                background-color: rgba(30, 41, 59, 0.70);
                border: 1px solid rgba(148, 163, 184, 0.15);
                border-radius: 20px;
            }
            QLabel {
                color: #e0e0e0;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel[role="heading"] {
                font-size: 20px;
                font-weight: 700;
                color: #F8FAFC;
            }
            QLabel[role="subtitle"] {
                font-size: 13px;
                color: #94A3B8;
            }
            QLineEdit {
                background-color: rgba(15, 23, 42, 0.6);
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 10px 14px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #38BDF8;
                background-color: rgba(15, 23, 42, 0.9);
            }
            QPushButton {
                border-radius: 10px;
                padding: 10px;
                font-weight: 600;
            }
            QPushButton[class="primary"] {
                background-color: #3B82F6;
                color: white;
                border: 1px solid #2563EB;
            }
            QPushButton[class="primary"]:hover {
                background-color: #60A5FA;
            }
            QPushButton[class="secondary"] {
                background-color: rgba(6, 182, 212, 0.15);
                color: #22D3EE;
                border: 1px solid #0891B2;
            }
            QPushButton[class="secondary"]:hover {
                background-color: rgba(6, 182, 212, 0.25);
                color: #67E8F9;
                border: 1px solid #22D3EE;
            }
            QPushButton[class="warning"] {
                background-color: rgba(245, 158, 11, 0.15);
                color: #FBBF24;
                border: 1px solid #D97706;
            }
            QPushButton[class="warning"]:hover {
                background-color: rgba(245, 158, 11, 0.25);
                color: #FDE68A;
                border: 1px solid #FBBF24;
            }
            QPushButton[class="danger"] {
                background-color: rgba(239, 68, 68, 0.15);
                color: #F87171;
                border: 1px solid #B91C1C;
            }
            QPushButton[class="danger"]:hover {
                background-color: rgba(239, 68, 68, 0.25);
                color: #FCA5A5;
                border: 1px solid #EF4444;
            }
            QTableWidget {
                background-color: rgba(15, 23, 42, 0.5);
                border: 1px solid #334155;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #334155;
                color: #E2E8F0;
            }
            QTableWidget::item:selected {
                background-color: rgba(56, 189, 248, 0.2);
                color: white;
            }
            QHeaderView::section {
                background-color: #0F172A;
                padding: 12px;
                border: none;
                border-bottom: 2px solid #334155;
                font-weight: 700;
                color: #94A3B8;
            }
        """)

        cards_layout = QHBoxLayout(self.cards_container)
        cards_layout.setContentsMargins(40, 40, 40, 40)
        cards_layout.setSpacing(40)
        # Center horizontally and allow top alignment (looks like rows) or Center both
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        scroll.setWidget(self.cards_container)
        main_layout.addWidget(scroll)

        # --- Profile Card ---
        self.card = QWidget()
        self.card.setSizePolicy(
            QSizePolicy.Policy.Fixed, 
            QSizePolicy.Policy.Fixed
        )
        self.card.setProperty("class", "card")
        self.card.setFixedWidth(480) # Increased width
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)
        
        # --- Header ---
        header_layout = QVBoxLayout()
        header_layout.setSpacing(6)
        
        lbl_title = QLabel("Configuración de Perfil")
        lbl_title.setProperty("role", "heading")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_desc = QLabel("Administra tus credenciales y acceso biométrico")
        lbl_desc.setProperty("role", "subtitle")
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(lbl_title)
        header_layout.addWidget(lbl_desc)
        card_layout.addLayout(header_layout)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #334155; height: 1px; border: none;")
        card_layout.addWidget(line)
        
        # --- Form Section ---
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)
        
        # User Field
        lbl_user = QLabel("Usuario")
        lbl_user.setStyleSheet("font-weight: 600; color: #E2E8F0; margin-bottom: 4px;")
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Ingresa tu usuario")
        self.user_input.setMinimumHeight(38)
        
        form_layout.addWidget(lbl_user)
        form_layout.addWidget(self.user_input)
        
        # Password Field
        lbl_pass = QLabel("Contraseña")
        lbl_pass.setStyleSheet("font-weight: 600; color: #E2E8F0; margin-bottom: 4px;")
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Dejar vacía para mantener actual")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setMinimumHeight(38)
        
        # Container for pass + toggle
        pass_container = QWidget()
        pass_layout = QHBoxLayout(pass_container)
        pass_layout.setContentsMargins(0,0,0,0)
        pass_layout.setSpacing(8)
        
        pass_layout.addWidget(self.pass_input)
        
        self.btn_toggle_pass = QPushButton("👁")
        self.btn_toggle_pass.setFixedWidth(50)
        self.btn_toggle_pass.setMinimumHeight(38)
        self.btn_toggle_pass.setToolTip("Mostrar/Ocultar contraseña")
        self.btn_toggle_pass.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_pass.setCheckable(True)
        self.btn_toggle_pass.clicked.connect(self.on_toggle_password)
        self.btn_toggle_pass.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 41, 59, 0.6);
                border: 1px solid #334155;
                font-size: 16px;
                border-radius: 10px;
                color: #94A3B8;
            }
            QPushButton:checked {
                 color: #38BDF8;
                 border-color: #38BDF8;
                 background-color: rgba(56, 189, 248, 0.1);
            }
        """)

        pass_layout.addWidget(self.btn_toggle_pass)
        
        form_layout.addWidget(lbl_pass)
        form_layout.addWidget(pass_container)
        
        card_layout.addLayout(form_layout)
        
        # Save Button
        self.btn_save = QPushButton("Guardar Cambios")
        self.btn_save.setMinimumHeight(40)
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setProperty("class", "primary")
        self.btn_save.clicked.connect(self.on_save_profile)
        card_layout.addWidget(self.btn_save)

        # Biometrics Section
        bio_group = QVBoxLayout()
        bio_group.setSpacing(8)
        
        lbl_bio = QLabel("Seguridad Biométrica")
        lbl_bio.setStyleSheet("font-weight: 600; color: #E2E8F0; margin-top: 8px;")
        bio_group.addWidget(lbl_bio)

        bio_btns = QHBoxLayout()
        bio_btns.setSpacing(12)
        
        self.btn_bio = QPushButton(" Configurar Facial")
        self.btn_bio.setMinimumHeight(38)
        self.btn_bio.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_bio.setProperty("class", "secondary")
        self.btn_bio.setIcon(load_icon("scan.svg"))
        self.btn_bio.clicked.connect(self.on_config_bio)
        
        self.btn_del_bio = QPushButton(" Borrar")
        self.btn_del_bio.setMinimumHeight(38)
        self.btn_del_bio.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_del_bio.setProperty("class", "danger")
        self.btn_del_bio.setIcon(load_icon("scan.svg")) 
        self.btn_del_bio.clicked.connect(self.on_delete_bio)
        
        bio_btns.addWidget(self.btn_bio, 2)
        bio_btns.addWidget(self.btn_del_bio, 1)
        
        bio_group.addLayout(bio_btns)
        card_layout.addLayout(bio_group)

        # --- Danger Zone Spacer ---
        card_layout.addSpacing(4)
        
        # Separator (Danger Zone)
        self.danger_line = QFrame()
        self.danger_line.setFrameShape(QFrame.Shape.HLine)
        self.danger_line.setStyleSheet("background-color: #334155; height: 1px; border: none;")
        card_layout.addWidget(self.danger_line)
        
        # --- Danger Zone ---
        danger_layout = QHBoxLayout()
        danger_layout.setSpacing(12)
        
        self.warn_icon = QLabel("⚠️")
        self.warn_icon.setStyleSheet("font-size: 20px;")
        
        self.warn_text = QLabel("Zona de Peligro")
        self.warn_text.setStyleSheet("font-weight: 700; color: #EF4444; font-size: 14px;")
        
        danger_layout.addWidget(self.warn_icon)
        danger_layout.addWidget(self.warn_text)
        danger_layout.addStretch(1)
        
        card_layout.addLayout(danger_layout)
        
        self.btn_delete = QPushButton("Eliminar mi cuenta")
        self.btn_delete.setMinimumHeight(38)
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.setProperty("class", "danger")
        self.btn_delete.clicked.connect(self.on_delete_account)
        card_layout.addWidget(self.btn_delete)
        
        cards_layout.addStretch(1) # Leading stretch
        cards_layout.addWidget(self.card)

        # --- Admin Section (Users List) ---
        self.admin_card = QWidget()
        self.admin_card.setSizePolicy(
            QSizePolicy.Policy.Fixed, 
            QSizePolicy.Policy.Fixed
        )
        self.admin_card.setProperty("class", "card")
        self.admin_card.setFixedWidth(540) # Slightly wider
        admin_layout = QVBoxLayout(self.admin_card)
        admin_layout.setContentsMargins(24, 24, 24, 24)
        admin_layout.setSpacing(16)
        
        lbl_admin = QLabel("Administración de Usuarios")
        lbl_admin.setProperty("role", "heading")
        admin_layout.addWidget(lbl_admin)

        self.user_table = QTableWidget(0, 2)
        self.user_table.setHorizontalHeaderLabels(["ID", "Usuario"])
        self.user_table.verticalHeader().setVisible(False)
        self.user_table.setShowGrid(False)
        self.user_table.setFrameShape(QFrame.Shape.NoFrame)
        self.user_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.user_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.user_table.setColumnHidden(0, True)
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.user_table.setMinimumHeight(200)
        self.user_table.setProperty("class", "premium-table")
        
        admin_layout.addWidget(self.user_table)
        
        # User Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.btn_edit_user = QPushButton("Editar Usuario")
        self.btn_edit_user.setMinimumHeight(38)
        self.btn_edit_user.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_edit_user.setProperty("class", "warning")
        self.btn_edit_user.clicked.connect(self.on_edit_user)
        
        self.btn_del_user = QPushButton("Eliminar Usuario")
        self.btn_del_user.setMinimumHeight(38)
        self.btn_del_user.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_del_user.setProperty("class", "danger")
        self.btn_del_user.clicked.connect(self.on_delete_user)
        
        btn_layout.addWidget(self.btn_edit_user)
        btn_layout.addWidget(self.btn_del_user)
        admin_layout.addLayout(btn_layout)
        
        cards_layout.addWidget(self.admin_card)
        cards_layout.addStretch(1) # Trailing stretch for centering both


        

        # Init functionality
        self.refresh()
    
    def on_toggle_password(self, checked):
        if checked:
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)

    def title(self):
        return "Configuración"

    def refresh(self):
        current_user = session.CURRENT_USER or ""
        is_admin = (current_user == "DI-ADMIN")

        # Load current user profile
        self.user_input.setText(current_user)
        self.pass_input.clear()
        
        # Protect Admin Account
        if is_admin:
            self.btn_delete.setVisible(False)
            self.user_input.setReadOnly(True)
            # Ocultar zona de peligro para administrador
            self.danger_line.setVisible(False)
            self.warn_icon.setVisible(False)
            self.warn_text.setVisible(False)
        else:
            self.btn_delete.setVisible(True)
            self.user_input.setReadOnly(False)
            # Mostrar zona de peligro para usuarios no administradores
            self.danger_line.setVisible(True)
            self.warn_icon.setVisible(True)
            self.warn_text.setVisible(True)

        # Toggle Admin Panel
        if is_admin:
            self.admin_card.setVisible(True)
            self.load_users()
        else:
            self.admin_card.setVisible(False)

    def load_users(self):
        users = list_users_full()
        self.user_table.setRowCount(0)
        # Filter out DI-ADMIN
        visible_users = [u for u in users if u.username != "DI-ADMIN"]
        
        for u in visible_users:
            r = self.user_table.rowCount()
            self.user_table.insertRow(r)
            self.user_table.setItem(r, 0, QTableWidgetItem(str(u.id)))
            self.user_table.setItem(r, 1, QTableWidgetItem(u.username))

    def on_save_profile(self):
        new_user = self.user_input.text().strip()
        new_pass = self.pass_input.text().strip()
        
        if not new_user:
            QMessageBox.warning(self, "Error", "El nombre de usuario no puede estar vacío.")
            return
            
        current_username = session.CURRENT_USER
        if not current_username:
            return

        u = get_user(current_username)
        if not u:
            return

        data = {}
        if new_user != current_username:
            data['username'] = new_user
        if new_pass:
            if not validate_password_strength(new_pass):
                QMessageBox.warning(
                    self, 
                    "Contraseña Débil", 
                    "La contraseña debe tener al menos una letra MAYÚSCULA, un número y un carácter especial."
                )
                return
            data['password'] = new_pass
            
        if not data:
            return

        # Solicitar permisos de administrador solo si se cambia el nombre de usuario
        # Si el usuario actual YA es el administrador principal, no se pide de nuevo
        if 'username' in data and session.CURRENT_USER != "DI-ADMIN":
            motivo = "Para cambiar el nombre de usuario se requieren permisos de administrador."
            dlg = AdminAuthDialog(self, motivo)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                QMessageBox.information(self, "Permisos", "Operación cancelada. No se modificaron las credenciales.")
                return

        try:
            update_user_profile(u.id, data)
            QMessageBox.information(self, "Éxito", "Perfil actualizado correctamente.")
            
            # Logging
            if 'username' in data:
                 try: add_bitacora_log(u.id, "Cambio de Usuario", f"Nombre cambiado de '{current_username}' a '{new_user}'", "Configuracion")
                 except: pass
            if 'password' in data:
                 try: add_bitacora_log(u.id, "Cambio de Contraseña", "El usuario actualizó su contraseña", "Seguridad")
                 except: pass

            if 'username' in data:
                session.CURRENT_USER = new_user
                self.refresh()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar: {e}")

    def on_config_bio(self):
        u = get_user(session.CURRENT_USER)
        if not u: return
        dlg = FaceCaptureDialog(u.id, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
             try: add_bitacora_log(u.id, "Registro Facial", "Se configuraron datos biométricos", "Seguridad")
             except: pass

    def on_delete_bio(self):
        u = get_user(session.CURRENT_USER)
        if not u: return
        
        if not u.face_data:
            QMessageBox.information(self, "Biometría", "No tienes datos biométricos configurados.")
            return

        res = QMessageBox.question(
            self,
            "Borrar Biometría",
            "¿Estás seguro de que deseas eliminar tus datos de reconocimiento facial?\nNo podrás usar el inicio de sesión con rostro.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res == QMessageBox.StandardButton.Yes:
            try:
                update_user_profile(u.id, {"face_data": None})
                try: add_bitacora_log(u.id, "Eliminar Facial", "Se borraron datos biométricos", "Seguridad")
                except: pass
                QMessageBox.information(self, "Biometría", "Datos faciales eliminados correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar: {e}")

    def on_delete_account(self):
        if session.CURRENT_USER == "DI-ADMIN":
            QMessageBox.warning(self, "Acción Denegada", "El usuario administrador principal no puede ser eliminado.")
            return
        # Solicitar permisos de administrador antes de eliminar la cuenta
        # Si el usuario actual YA es el administrador principal, no se pide de nuevo
        if session.CURRENT_USER != "DI-ADMIN":
            motivo = "Para eliminar una cuenta se requieren permisos de administrador."
            auth = AdminAuthDialog(self, motivo)
            if auth.exec() != QDialog.DialogCode.Accepted:
                QMessageBox.information(self, "Permisos", "Operación cancelada. No se eliminó la cuenta.")
                return

        res = QMessageBox.warning(
            self, 
            "Eliminar Cuenta", 
            "¿Estás seguro de que deseas ELIMINAR tu cuenta?\nEsta acción no se puede deshacer y cerrarás sesión inmediatamente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res == QMessageBox.StandardButton.Yes:
            u = get_user(session.CURRENT_USER)
            if u:
                delete_user(u.id)
                window = self.window()
                if hasattr(window, 'on_logout'):
                    window.on_logout()

    def get_selected_user(self):
        rows = self.user_table.selectionModel().selectedRows()
        if not rows:
            return None
        # Get ID from hidden column 0
        user_id = int(self.user_table.item(rows[0].row(), 0).text())
        # Find user object
        users = list_users_full() # Cached or fresh? Fresh is safer
        for u in users:
            if u.id == user_id:
                return u
        return None

    def on_edit_user(self):
        u = self.get_selected_user()
        if not u:
            QMessageBox.warning(self, "Selección", "Selecciona un usuario de la lista.")
            return
            
        dlg = UserEditDialog(u, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                current_admin = get_user(session.CURRENT_USER)
                aid = current_admin.id if current_admin else None
                add_bitacora_log(aid, "Editar Usuario Admin", f"Se editó el usuario '{u.username}' (ID: {u.id})", "Configuracion")
            except: pass
            self.load_users() # Refresh
            
    def on_delete_user(self):
        u = self.get_selected_user()
        if not u:
            QMessageBox.warning(self, "Selección", "Selecciona un usuario de la lista.")
            return
            
        res = QMessageBox.warning(
            self,
            "Eliminar Usuario",
            f"¿Estás seguro de que deseas eliminar al usuario '{u.username}'?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res == QMessageBox.StandardButton.Yes:
            if delete_user(u.id):
                try:
                    current_admin = get_user(session.CURRENT_USER)
                    aid = current_admin.id if current_admin else None
                    add_bitacora_log(aid, "Eliminar Usuario Admin", f"Se eliminó el usuario '{u.username}' (ID: {u.id})", "Configuracion")
                except: pass
                
                QMessageBox.information(self, "Éxito", "Usuario eliminado.")
                self.load_users()
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar el usuario.")

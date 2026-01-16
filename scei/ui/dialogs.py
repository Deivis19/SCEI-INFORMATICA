
import unicodedata
import re
from datetime import date
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton,
    QMessageBox, QWidget, QTextEdit, QComboBox, QDateEdit, QCompleter, QToolButton
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QSettings, QDate

from ..utils import load_pixmap, circular_pixmap, load_icon, validate_password_strength
from ..logger import add_log
from .. import session
from ..data.repositories import (
    add_equipo, update_equipo, get_equipo, list_equipos_by_direccion,
    add_mantenimiento, update_mantenimiento, get_mantenimiento,
    create_user, add_bitacora_log, get_user,
    check_user, set_user_password, list_direcciones, list_equipos, list_users,
    update_user_profile, delete_user
)
from .report_forms import EquiposReportForm, MantenimientosReportForm
from .biometrics import FaceLoginDialog
from sqlalchemy.exc import IntegrityError

class AdminAuthDialog(QDialog):
    """Diálogo genérico para solicitar permisos de administrador.

    Solo pide la contraseña del administrador (DI-ADMIN) y valida con check_user.
    No muestra ni solicita el nombre de usuario.
    """

    def __init__(self, parent=None, motivo: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("Permisos de administrador")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        lbl_title = QLabel("Permisos requeridos")
        lbl_title.setProperty("role", "heading")
        layout.addWidget(lbl_title)

        if motivo:
            lbl_motivo = QLabel(motivo)
            lbl_motivo.setWordWrap(True)
            lbl_motivo.setStyleSheet("color: #94A3B8; margin-bottom: 8px;")
            layout.addWidget(lbl_motivo)

        card = QWidget()
        card.setProperty("class", "card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(12)

        info = QLabel("Ingresa la contraseña del administrador para continuar.")
        info.setStyleSheet("color: #94A3B8;")
        info.setWordWrap(True)
        card_layout.addWidget(info)

        self.pass_admin = QLineEdit()
        self.pass_admin.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_admin.setPlaceholderText("Contraseña de administrador")
        card_layout.addWidget(self.pass_admin)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("class", "secondary")
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("Autorizar")
        btn_ok.setProperty("class", "primary")
        btn_ok.clicked.connect(self._on_accept)

        
        # Botón Facial
        btn_face = QPushButton()
        btn_face.setIcon(load_icon("scan.svg"))
        btn_face.setFixedSize(36, 36)
        btn_face.setProperty("class", "secondary")
        btn_face.setToolTip("Autorizar con rostro de Administrador")
        btn_face.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_face.clicked.connect(self.on_face_auth)

        btn_row.addWidget(btn_face)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        card_layout.addLayout(btn_row)

        layout.addWidget(card)

    def _on_accept(self):
        pwd = self.pass_admin.text()
        if not pwd:
            QMessageBox.warning(self, "Permisos", "Ingresa la contraseña del administrador.")
            return
        # Validar contra usuario administrador fijo
        if not check_user("DI-ADMIN", pwd):
            QMessageBox.warning(self, "Permisos", "Contraseña de administrador incorrecta.")
            return
        self.accept()

    def on_face_auth(self):
        # Usamos el mismo dialogo de Login Facil
        dlg = FaceLoginDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            user = dlg.authenticated_user
            if user == "DI-ADMIN":
                self.accept()
            else:
                QMessageBox.warning(self, "Autorización Fallida", "El rostro detectado NO pertenece al Administrador (DI-ADMIN).")


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setObjectName("LoginDialog")
        self.setWindowTitle("SCEI - Login")
        self.resize(1000, 650)
        
        # Window flags for a standard window feel
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.WindowSystemMenuHint |
            Qt.WindowType.WindowMinMaxButtonsHint | 
            Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowState(Qt.WindowState.WindowMaximized)
        
        # Main Horizontal Layout (Split Screen)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- LEFT PANEL (Illustration) ---
        self.left_panel = QWidget()
        self.left_panel.setStyleSheet("""
            QWidget {
                background-color: #020617; 
            }
            QLabel {
                color: #F8FAFC;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(40, 60, 40, 60)
        left_layout.setSpacing(20)
        
        # Welcome Text
        lbl_welcome = QLabel("BIENVENIDO")
        lbl_welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_welcome.setStyleSheet("font-size: 36px; font-weight: 900; letter-spacing: 2px; color: white;")
        left_layout.addWidget(lbl_welcome)
        
        # Illustration (Cyber Image)
        lbl_img = QLabel()
        lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = load_pixmap("cyber_ring_lock.png")
        if not pix.isNull():
            lbl_img.setPixmap(pix.scaled(350, 350, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            lbl_img.setText("🔐")
            lbl_img.setStyleSheet("font-size: 100px;")
        
        left_layout.addStretch(1)
        left_layout.addWidget(lbl_img)
        left_layout.addStretch(1)
        
        # Tagline
        lbl_system = QLabel("Sistema de Control de Equipos Informáticos")
        lbl_system.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_system.setStyleSheet("font-size: 16px; color: #94A3B8; font-weight: 500;")
        left_layout.addWidget(lbl_system)
        
        # --- RIGHT PANEL (Form) ---
        self.right_panel = QWidget()
        self.right_panel.setStyleSheet("""
            QWidget {
                background-color: #0F172A;
            }
            QLabel {
                color: #E2E8F0;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit, QComboBox {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 21px; /* Pill shape */
                padding: 10px 14px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #38BDF8;
                background-color: #1E293B;
            }
            QComboBox::drop-down { border: none; width: 30px; margin-right: 10px; }
            QPushButton {
                border-radius: 21px;
                font-weight: 700;
                font-size: 14px;
                padding: 10px;
            }
        """)
        
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(60, 60, 60, 60)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Container to center form content vertically
        form_container = QWidget()
        form_container.setMaximumWidth(320) # Restringir ancho para diseño más compacto
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(20)
        
        # User Icon Header
        icon_header = QLabel("👤")
        icon_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_header.setStyleSheet("""
            background-color: #3B82F6; 
            border-radius: 40px; 
            font-size: 40px; 
            padding: 10px;
            color: white;
        """)
        icon_header.setFixedSize(80, 80)
        
        # Wrapper for centering the icon
        icon_wrap = QHBoxLayout()
        icon_wrap.addStretch(1)
        icon_wrap.addWidget(icon_header)
        icon_wrap.addStretch(1)
        form_layout.addLayout(icon_wrap)
        
        # "Sign In" Text
        lbl_signin = QLabel("Iniciar Sesión")
        lbl_signin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_signin.setStyleSheet("font-size: 24px; font-weight: 700; margin-bottom: 10px; color: white;")
        form_layout.addWidget(lbl_signin)
        
        # Inputs
        # User Input
        input_box = QVBoxLayout()
        input_box.setSpacing(15)
        
        self.user = QComboBox()
        self.user.setEditable(True)
        self.user.lineEdit().setPlaceholderText("Usuario")
        self.user.setMinimumHeight(42)
        # Populate users
        try:
             users = [u for u in list_users() if u.upper() != "DI-ADMIN"]
             self.user.addItems(users)
        except: pass
        self.user.setCurrentIndex(-1)
        
        completer = QCompleter(users if 'users' in locals() else [])
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        # Apply style to completer popup for Dark Mode
        completer.popup().setStyleSheet("""
            QListView {
                background-color: #1E293B;
                color: white;
                border: 1px solid #334155;
                font-size: 14px;
                padding: 4px;
            }
            QListView::item {
                padding: 6px;
            }
            QListView::item:selected {
                background-color: #3B82F6;
                color: white;
            }
        """)
        self.user.setCompleter(completer)
        
        input_box.addWidget(self.user)
        
        # Password Input Layout (Pill shape container)
        pwd_container = QWidget()
        pwd_container.setStyleSheet("""
            QWidget {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 21px;
            }
        """)
        pwd_container.setMinimumHeight(42)
        pwd_layout = QHBoxLayout(pwd_container)
        pwd_layout.setContentsMargins(5, 5, 20, 5) # Right margin for icon
        
        self.passw = QLineEdit()
        self.passw.setPlaceholderText("Contraseña")
        self.passw.setEchoMode(QLineEdit.EchoMode.Password)
        self.passw.setStyleSheet("border: none; background: transparent; padding-left: 15px;")
        
        self.btn_eye = QToolButton()
        self.btn_eye.setText("👁")
        self.btn_eye.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_eye.setStyleSheet("background: transparent; border: none; font-size: 18px; color: #94A3B8;")
        self.btn_eye.clicked.connect(self._toggle_login_password)

        pwd_layout.addWidget(self.passw)
        pwd_layout.addWidget(self.btn_eye)
        
        input_box.addWidget(pwd_container)
        form_layout.addLayout(input_box)
        
        # Login Button
        btn_login = QPushButton("INGRESAR")
        btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_login.clicked.connect(self.try_login)
        btn_login.setStyleSheet("""
            QPushButton {
                background-color: rgba(6, 182, 212, 0.15);
                color: #22D3EE;
                border: 1px solid #0891B2;
                border-radius: 21px;
                font-weight: 800;
                font-size: 15px;
                padding: 10px;
                margin-top: 10px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: rgba(6, 182, 212, 0.25);
                color: #67E8F9;
                border: 1px solid #22D3EE;
            }
            QPushButton:pressed {
                background-color: rgba(6, 182, 212, 0.35);
                border: 1px solid #22D3EE;
            }
        """)
        form_layout.addWidget(btn_login)
        
        # Tools Links
        tools_layout = QVBoxLayout()
        tools_layout.setSpacing(10)
        tools_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Forgot / Change Password
        btn_forgot = QPushButton("¿Olvidaste tu contraseña?")
        btn_forgot.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_forgot.clicked.connect(self.on_change_password)
        btn_forgot.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94A3B8;
                font-size: 13px;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover { color: #38BDF8; }
        """)
        tools_layout.addWidget(btn_forgot)
        
        # Signup Row
        signup_row = QHBoxLayout()
        signup_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_no_acc = QLabel("¿No tienes cuenta?")
        lbl_no_acc.setStyleSheet("color: #64748B; font-size: 13px;")
        
        btn_signup = QPushButton("Regístrate ahora")
        btn_signup.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_signup.clicked.connect(self.on_register)
        btn_signup.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #38BDF8;
                font-weight: 700;
                font-size: 13px;
                border: none;
            }
            QPushButton:hover { text-decoration: underline; }
        """)
        
        signup_row.addWidget(lbl_no_acc)
        signup_row.addWidget(btn_signup)
        tools_layout.addLayout(signup_row)
        
        # Facial Login Button (Bottom)
        btn_face = QPushButton("   Ingreso Facial")
        btn_face.setIcon(load_icon("scan.svg"))
        btn_face.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_face.clicked.connect(self.on_face_login)
        btn_face.setStyleSheet("""
            QPushButton {
                background-color: rgba(56, 189, 248, 0.1);
                color: #38BDF8;
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 20px;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: rgba(56, 189, 248, 0.2);
            }
        """)
        
        tools_layout.addWidget(btn_face)
        
        form_layout.addLayout(tools_layout)
        
        right_layout.addWidget(form_container)

        # Add panels to split layout
        main_layout.addWidget(self.left_panel, 1) # 40% width approx (flex 1)
        main_layout.addWidget(self.right_panel, 1) # 60% width (flex 1, equal for now)

    def try_login(self):
        user = self.user.currentText().strip() or "DI-ADMIN"
        if check_user(user, self.passw.text()):
            settings = QSettings("SCEI", "App")
            settings.setValue("last_user", user)
            self.user.setCurrentText(user)
            session.CURRENT_USER = user
            add_log("Inicio de sesión", f"Usuario: {user}")
            # Log Bitacora
            u_obj = get_user(user)
            if u_obj:
                try: add_bitacora_log(u_obj.id, "Iniciaste sesión", "Inicio de sesión exitoso", "Sistema")
                except: pass
            
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Credenciales inválidas")

    def _toggle_login_password(self):
        if self.passw.echoMode() == QLineEdit.EchoMode.Password:
            self.passw.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_eye.setText("🔒")
        else:
            self.passw.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_eye.setText("👁")

    def on_change_password(self):
        dlg = ChangePasswordDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Contraseña", "Contraseña actualizada correctamente.")

    def on_register(self):
        dlg = RegisterDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Registro", "Usuario registrado exitosamente.")

    def on_face_login(self):
        dlg = FaceLoginDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            user = dlg.authenticated_user
            session.CURRENT_USER = user
            add_log("Inicio de sesión facial", f"Usuario: {user}")
            
            u_obj = get_user(user)
            if u_obj:
                try: add_bitacora_log(u_obj.id, "Auto Login", "Inicio de sesión biométrico", "Sistema")
                except: pass
                
            self.accept()

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registro de Usuario")
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        lbl_header = QLabel("Nuevo Usuario")
        lbl_header.setProperty("role", "heading")
        layout.addWidget(lbl_header)
        
        lbl_hint = QLabel("(El nombre de usuario debe tener tu primer nombre y la inicial de Informática. Ejemplo: Deivis-I)")
        lbl_hint.setStyleSheet("font-size: 11px; color: #94A3B8; font-style: italic; margin-bottom: 8px;")
        lbl_hint.setWordWrap(True)
        layout.addWidget(lbl_hint)
        
        card = QWidget()
        card.setProperty("class", "card")
        c = QVBoxLayout(card)
        c.setSpacing(12)
        
        self.user = QLineEdit(); self.user.setPlaceholderText("Usuario (login)")
        
        # Password with eye toggle
        from PyQt6.QtWidgets import QToolButton
        from PyQt6.QtCore import QSize
        
        self.pwd = QLineEdit()
        self.pwd.setPlaceholderText("Contraseña")
        self.pwd.setEchoMode(QLineEdit.EchoMode.Password)
        
        pwd_row = QHBoxLayout()
        pwd_row.setSpacing(4)
        pwd_row.addWidget(self.pwd)
        self.btn_eye1 = QToolButton()
        self.btn_eye1.setText("👁")
        self.btn_eye1.setStyleSheet("QToolButton { border: none; background: transparent; font-size: 16px; }")
        self.btn_eye1.clicked.connect(lambda: self._toggle_pass(self.pwd, self.btn_eye1))
        pwd_row.addWidget(self.btn_eye1)
        
        self.pwd2 = QLineEdit()
        self.pwd2.setPlaceholderText("Confirmar Contraseña")
        self.pwd2.setEchoMode(QLineEdit.EchoMode.Password)
        
        pwd2_row = QHBoxLayout()
        pwd2_row.setSpacing(4)
        pwd2_row.addWidget(self.pwd2)
        self.btn_eye2 = QToolButton()
        self.btn_eye2.setText("👁")
        self.btn_eye2.setStyleSheet("QToolButton { border: none; background: transparent; font-size: 16px; }")
        self.btn_eye2.clicked.connect(lambda: self._toggle_pass(self.pwd2, self.btn_eye2))
        pwd2_row.addWidget(self.btn_eye2)
        
        c.addWidget(QLabel("Usuario")); c.addWidget(self.user)
        c.addWidget(QLabel("Contraseña")); c.addLayout(pwd_row)
        c.addLayout(pwd2_row)
        
        # Security Questions Section
        c.addSpacing(10)
        lbl_sec = QLabel("Preguntas de Seguridad")
        lbl_sec.setStyleSheet("font-weight: 600; color: #94A3B8; margin-top: 8px;")
        c.addWidget(lbl_sec)
        
        lbl_q1 = QLabel("¿Qué día y mes cumples años? (DD/MM)")
        lbl_q1.setStyleSheet("font-size: 12px; color: #E2E8F0;")
        self.sec_q1 = QLineEdit()
        self.sec_q1.setPlaceholderText("Ejemplo: 15/03")
        c.addWidget(lbl_q1)
        c.addWidget(self.sec_q1)
        
        lbl_q2 = QLabel("Nombre de papá o mamá (en minúsculas)")
        lbl_q2.setStyleSheet("font-size: 12px; color: #E2E8F0;")
        self.sec_q2 = QLineEdit()
        self.sec_q2.setPlaceholderText("Ejemplo: maria")
        c.addWidget(lbl_q2)
        c.addWidget(self.sec_q2)
        
        c.addSpacing(10)
        btn_row = QHBoxLayout(); btn_row.addStretch(1)
        btn_sav = QPushButton("Registrar"); btn_sav.setProperty("class", "primary")
        btn_can = QPushButton("Cancelar"); btn_can.setProperty("class", "secondary")
        
        btn_sav.clicked.connect(self.on_save)
        btn_can.clicked.connect(self.reject)
        
        btn_row.addWidget(btn_can); btn_row.addWidget(btn_sav)
        c.addLayout(btn_row)
        layout.addWidget(card)
    
    def _toggle_pass(self, field: QLineEdit, btn: QToolButton):
        if field.echoMode() == QLineEdit.EchoMode.Password:
            field.setEchoMode(QLineEdit.EchoMode.Normal)
            btn.setText("🔒")
        else:
            field.setEchoMode(QLineEdit.EchoMode.Password)
            btn.setText("👁")
        
    def on_save(self):
        u = self.user.text().strip()
        p = self.pwd.text()
        p2 = self.pwd2.text()
        q1 = self.sec_q1.text().strip()
        q2 = self.sec_q2.text().strip().lower()
        
        if not u or not p:
            QMessageBox.warning(self, "Error", "Usuario y contraseña requeridos")
            return
        if p != p2:
            QMessageBox.warning(self, "Error", "Las contraseñas no coinciden")
            return
        if not validate_password_strength(p):
            QMessageBox.warning(self, "Seguridad", "La contraseña es muy débil (Mayús, núm, especial).")
            return
        if not q1 or not q2:
            QMessageBox.warning(self, "Seguridad", "Debes responder las preguntas de seguridad.")
            return

        if not re.match(r"^\d{2}/\d{2}$", q1):
             QMessageBox.warning(self, "Seguridad", "La fecha de cumpleaños debe tener el formato DD/MM (ej. 15/03).")
             return
            
        try:
            data = {
                "username": u,
                "password": p,
                "nombre_completo": None,
                "email": None,
                "rol": "usuario",
                "respuesta_seguridad_1": q1,
                "respuesta_seguridad_2": q2
            }
            create_user(data)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al registrar: {e}")

class ChangePasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cambio de Contraseña")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        lbl_header = QLabel("Seguridad de la Cuenta")
        lbl_header.setProperty("role", "heading")
        layout.addWidget(lbl_header)

        card = QWidget()
        card.setProperty("class", "card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(12)

        lbl_info = QLabel("Ingresa tu usuario y responde las preguntas de seguridad.")
        lbl_info.setStyleSheet("color: #94A3B8; margin-bottom: 8px;")
        lbl_info.setWordWrap(True)
        card_layout.addWidget(lbl_info)
        
        # Usuario a cambiar
        card_layout.addWidget(QLabel("Usuario"))
        self.target_user = QLineEdit()
        self.target_user.setPlaceholderText("Nombre de usuario")
        self.target_user.textChanged.connect(self._on_user_changed)
        card_layout.addWidget(self.target_user)

        # Questions Container (will be updated dynamically)
        self.questions_widget = QWidget()
        self.questions_layout = QVBoxLayout(self.questions_widget)
        self.questions_layout.setContentsMargins(0, 0, 0, 0)
        self.questions_layout.setSpacing(8)
        
        # Pregunta 1
        self.lbl_q1 = QLabel("")
        self.q1 = QLineEdit()
        self.questions_layout.addWidget(self.lbl_q1)
        self.questions_layout.addWidget(self.q1)

        # Pregunta 2
        self.lbl_q2 = QLabel("")
        self.q2 = QLineEdit()
        self.questions_layout.addWidget(self.lbl_q2)
        self.questions_layout.addWidget(self.q2)
        
        card_layout.addWidget(self.questions_widget)

        card_layout.addSpacing(8)
        lbl_rules = QLabel(
            "La nueva contraseña debe tener: Mayúscula, Número y Carácter Especial."
        )
        lbl_rules.setStyleSheet("font-size: 11px; color: #64748B; font-style: italic;")
        lbl_rules.setWordWrap(True)
        card_layout.addWidget(lbl_rules)

        # Passwords with eye toggle
        from PyQt6.QtWidgets import QToolButton
        
        self.new_pass = QLineEdit()
        self.new_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pass.setPlaceholderText("Nueva contraseña")
        self.new_pass2 = QLineEdit()
        self.new_pass2.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pass2.setPlaceholderText("Confirmar contraseña")
        
        row_p1 = QHBoxLayout()
        row_p1.setSpacing(4)
        row_p1.addWidget(self.new_pass)
        self.btn_eye1 = QToolButton()
        self.btn_eye1.setText("👁")
        self.btn_eye1.setStyleSheet("QToolButton { border: none; background: transparent; font-size: 16px; }")
        self.btn_eye1.clicked.connect(self._toggle_new_pass1)
        row_p1.addWidget(self.btn_eye1)
        card_layout.addLayout(row_p1)

        row_p2 = QHBoxLayout()
        row_p2.setSpacing(4)
        row_p2.addWidget(self.new_pass2)
        self.btn_eye2 = QToolButton()
        self.btn_eye2.setText("👁")
        self.btn_eye2.setStyleSheet("QToolButton { border: none; background: transparent; font-size: 16px; }")
        self.btn_eye2.clicked.connect(self._toggle_new_pass2)
        row_p2.addWidget(self.btn_eye2)
        card_layout.addLayout(row_p2)

        card_layout.addSpacing(10)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_ca = QPushButton("Cancelar")
        btn_ca.setProperty("class", "secondary")
        btn_ca.clicked.connect(self.reject)
        btn_ok = QPushButton("Actualizar")
        btn_ok.setProperty("class", "primary")
        btn_ok.clicked.connect(self.on_accept)
        
        btn_row.addWidget(btn_ca)
        btn_row.addWidget(btn_ok)
        card_layout.addLayout(btn_row)

        layout.addWidget(card)
        
        # Initialize with empty state
        self._update_questions_for_user("")

    def _on_user_changed(self, text: str):
        self._update_questions_for_user(text.strip())
    
    def _update_questions_for_user(self, username: str):
        """Update visible questions based on the target user."""
        if username.upper() == "DI-ADMIN":
            # Admin questions (hardcoded)
            self.lbl_q1.setText("¿CUÁL ES EL DÍA DEL INGENIERO EN VENEZUELA?")
            self.q1.setPlaceholderText("Ejemplo: 28/10")
            self.lbl_q2.setText("¿Cuál es tu número de CIV?")
            self.q2.setPlaceholderText("Ejemplo: 238006")
        else:
            # Regular user questions
            self.lbl_q1.setText("¿Qué día y mes cumples años? (DD/MM)")
            self.q1.setPlaceholderText("Ejemplo: 15/03")
            self.lbl_q2.setText("Nombre de papá o mamá (en minúsculas)")
            self.q2.setPlaceholderText("Ejemplo: maria")
        
        # Clear answers when user changes
        self.q1.clear()
        self.q2.clear()

    def _normalize_name(self, text: str) -> str:
        txt = text.strip().lower()
        nfkd = unicodedata.normalize('NFKD', txt)
        no_accents = ''.join(c for c in nfkd if not unicodedata.combining(c))
        parts = no_accents.split()
        return ' '.join(parts)

    def on_accept(self):
        target_u = self.target_user.text().strip()
        
        if not target_u:
            QMessageBox.warning(self, "Error", "Ingresa el nombre de usuario.")
            return
        
        # Fetch user to validate answers
        user_obj = get_user(target_u)
        if not user_obj:
            QMessageBox.warning(self, "Error", f"El usuario '{target_u}' no existe.")
            return

        # Solicitar permisos de administrador antes de permitir el cambio de contraseña
        # Si el usuario YA es DI-ADMIN (sesión actual), no se pide de nuevo

        
        q1_ans = self.q1.text().strip()
        q2_ans = self.q2.text().strip()
        
        # Validate answers based on user type
        if target_u.upper() == "DI-ADMIN":
            # Admin validation (hardcoded answers)
            if q1_ans != "28/10":
                QMessageBox.warning(self, "Seguridad", "Respuesta incorrecta a la primera pregunta.")
                return
            q2_digits = ''.join(c for c in q2_ans if c.isdigit())
            if q2_digits != "238006":
                QMessageBox.warning(self, "Seguridad", "Respuesta incorrecta a la segunda pregunta.")
                return
        else:
            # Regular user validation (from DB)
            stored_q1 = user_obj.respuesta_seguridad_1 or ""
            stored_q2 = user_obj.respuesta_seguridad_2 or ""
            
            if not stored_q1 or not stored_q2:
                QMessageBox.warning(self, "Error", "Este usuario no tiene preguntas de seguridad configuradas. Contacte al administrador.")
                return
            
            if q1_ans != stored_q1:
                QMessageBox.warning(self, "Seguridad", "Respuesta incorrecta a la primera pregunta.")
                return
            if q2_ans.lower() != stored_q2.lower():
                QMessageBox.warning(self, "Seguridad", "Respuesta incorrecta a la segunda pregunta.")
                return
        
        # Validate passwords
        if not self.new_pass.text() or not self.new_pass2.text():
            QMessageBox.warning(self, "Contraseña", "Ingresa y repite la nueva contraseña.")
            return
        if self.new_pass.text() != self.new_pass2.text():
            QMessageBox.warning(self, "Contraseña", "Las contraseñas no coinciden.")
            return
        if not validate_password_strength(self.new_pass.text()):
            QMessageBox.warning(
                self,
                "Contraseña",
                "La contraseña debe tener al menos una letra MAYÚSCULA, un número y un carácter especial.",
            )
            return
        
        ok = set_user_password(target_u, self.new_pass.text())
        if not ok:
            QMessageBox.critical(self, "Error", f"No se pudo actualizar la contraseña.")
            return
        self.accept()

    def _toggle_new_pass1(self):
        if self.new_pass.echoMode() == QLineEdit.EchoMode.Password:
            self.new_pass.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_eye1.setText("🔒")
        else:
            self.new_pass.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_eye1.setText("👁")

    def _toggle_new_pass2(self):
        if self.new_pass2.echoMode() == QLineEdit.EchoMode.Password:
            self.new_pass2.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_eye2.setText("🔒")
        else:
            self.new_pass2.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_eye2.setText("👁")



class DepartamentoDialog(QDialog):
    def __init__(self, codigo: str = "", nombre: str = ""):
        super().__init__()
        self.setWindowTitle("Departamento")
        v = QVBoxLayout()
        self.ed_codigo = QLineEdit(codigo)
        self.ed_nombre = QLineEdit(nombre)
        v.addWidget(QLabel("Código")); v.addWidget(self.ed_codigo)
        v.addWidget(QLabel("Nombre")); v.addWidget(self.ed_nombre)
        h = QHBoxLayout()
        self.btn_ok = QPushButton("Guardar"); self.btn_cancel = QPushButton("Cancelar")
        self.btn_ok.clicked.connect(self.accept); self.btn_cancel.clicked.connect(self.reject)
        h.addWidget(self.btn_ok); h.addWidget(self.btn_cancel)
        v.addLayout(h); self.setLayout(v)
        self.ed_nombre.returnPressed.connect(self.accept)

    def values(self):
        return self.ed_codigo.text().strip(), self.ed_nombre.text().strip()

class DireccionDialog(QDialog):
    def __init__(self, nombre: str = ""):
        super().__init__()
        self.setWindowTitle("Gestión de Dirección")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        lbl = QLabel("Datos de la Dirección")
        lbl.setProperty("role", "heading")
        layout.addWidget(lbl)

        card = QWidget()
        card.setProperty("class", "card")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(24, 24, 24, 24)
        c_layout.setSpacing(16)

        self.ed_nombre = QLineEdit(nombre)
        self.ed_nombre.setPlaceholderText("Nombre de la Dirección")
        c_layout.addWidget(QLabel("Nombre"))
        c_layout.addWidget(self.ed_nombre)

        btns = QHBoxLayout()
        btns.addStretch(1)
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setProperty("class", "secondary")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok = QPushButton("Guardar")
        self.btn_ok.setProperty("class", "primary")
        self.btn_ok.clicked.connect(self.accept)
        
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)
        c_layout.addLayout(btns)

        layout.addWidget(card)
        self.ed_nombre.returnPressed.connect(self.accept)

    def values(self):
        return self.ed_nombre.text().strip()

class EquipoDialog(QDialog):
    def __init__(self, direccion_filter: int | None = None, data: dict | None = None):
        super().__init__()
        self.setWindowTitle("Gestión de Equipos")
        self.setMinimumWidth(550)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Encabezado
        lbl_header = QLabel("Datos del Equipo")
        lbl_header.setProperty("role", "heading")
        # lbl_header.setStyleSheet("margin-bottom: 12px;") # Opcional si se quiere mas espacio
        layout.addWidget(lbl_header)

        # Tarjeta contenedora del formulario
        card = QWidget()
        card.setProperty("class", "card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)

        self.ed_codigo = QLineEdit(data.get("codigo_interno", "") if data else "")
        self.ed_codigo.setPlaceholderText("Ej: PC-001")
        
        self.ed_desc = QTextEdit(data.get("descripcion", "") if data else "")
        self.ed_desc.setPlaceholderText("Descripción técnica del equipo...")
        self.ed_desc.setFixedHeight(60)
        
        self.ed_marca = QLineEdit(data.get("marca", "") if data else "")
        self.ed_marca.setPlaceholderText("Marca")
        
        self.ed_modelo = QLineEdit(data.get("modelo", "") if data else "")
        self.ed_modelo.setPlaceholderText("Modelo")
        
        self.ed_serie = QLineEdit(data.get("nro_serie", "") if data else "")
        self.ed_serie.setPlaceholderText("Nº de Serie")
        
        self.cb_estado = QComboBox()
        self.cb_estado.addItems(["optimo", "defectuoso", "inoperativo"])
        if data and data.get("estado"):
            self.cb_estado.setCurrentText(data["estado"])
            
        self.cb_dir = QComboBox()
        dirs = list_direcciones()
        self.cb_dir.addItem("Seleccione Dirección...", None)
        for d in dirs:
            self.cb_dir.addItem(d.nombre, d.id)
            
        if direccion_filter:
            idx = self.cb_dir.findData(direccion_filter)
            if idx >= 0: self.cb_dir.setCurrentIndex(idx)
            self.cb_dir.setEnabled(False)
        elif data and data.get("direccion_id"):
            idx = self.cb_dir.findData(data["direccion_id"])
            if idx >= 0: self.cb_dir.setCurrentIndex(idx)
        
        # Fila 1: Código y Estado
        row1 = QHBoxLayout()
        
        col_cod = QVBoxLayout(); col_cod.setSpacing(6)
        col_cod.addWidget(QLabel("Código Interno"))
        col_cod.addWidget(self.ed_codigo)
        
        col_est = QVBoxLayout(); col_est.setSpacing(6)
        col_est.addWidget(QLabel("Estado Operativo"))
        col_est.addWidget(self.cb_estado)
        
        row1.addLayout(col_cod, 1)
        row1.addLayout(col_est, 1)
        card_layout.addLayout(row1)

        # Fila 2: Descripción
        col_desc = QVBoxLayout(); col_desc.setSpacing(6)
        col_desc.addWidget(QLabel("Descripción"))
        col_desc.addWidget(self.ed_desc)
        card_layout.addLayout(col_desc)

        # Fila 3: Detalles Técnicos (Marca, Modelo, Serie)
        row_tech = QHBoxLayout()
        row_tech.setSpacing(12)
        
        for lbl, widget in [("Marca", self.ed_marca), ("Modelo", self.ed_modelo), ("Nº Serie", self.ed_serie)]:
            c = QVBoxLayout(); c.setSpacing(6)
            c.addWidget(QLabel(lbl))
            c.addWidget(widget)
            row_tech.addLayout(c)
        card_layout.addLayout(row_tech)

        # Fila 4: Ubicación
        col_dir = QVBoxLayout(); col_dir.setSpacing(6)
        col_dir.addWidget(QLabel("Ubicación / Dirección"))
        col_dir.addWidget(self.cb_dir)
        card_layout.addLayout(col_dir)

        # Separador visual (opcional, o solo espacio)
        card_layout.addSpacing(10)

        # Botones de Acción
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("class", "secondary")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("Guardar Equipo")
        btn_save.setProperty("class", "primary")
        btn_save.clicked.connect(self.accept)
        
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        
        card_layout.addLayout(btn_row)
        layout.addWidget(card)

    def values(self) -> dict:
        return {
            "codigo_interno": self.ed_codigo.text().strip(),
            "descripcion": self.ed_desc.toPlainText().strip(),
            "marca": self.ed_marca.text().strip(),
            "modelo": self.ed_modelo.text().strip(),
            "nro_serie": self.ed_serie.text().strip(),
            "estado": self.cb_estado.currentText(),
            "direccion_id": self.cb_dir.currentData(),
        }

class MantenimientoDialog(QDialog):
    def __init__(self, direccion_filter: int | None = None, data: dict | None = None):
        super().__init__()
        self.setWindowTitle("Registro de Mantenimiento")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        lbl_header = QLabel("Detalles del Mantenimiento")
        lbl_header.setProperty("role", "heading")
        layout.addWidget(lbl_header)

        card = QWidget()
        card.setProperty("class", "card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)

        # Equipo Selector
        self.cb_equipo = QComboBox()
        equipos = list_equipos_by_direccion(direccion_filter) if direccion_filter else list_equipos()
        self.cb_equipo.addItem("Seleccione Equipo...", None)
        
        display_texts = []
        for e in equipos:
            text = f"{e.codigo_interno or ''} - {e.descripcion or ''} - {e.marca or ''}".strip().strip(" -")
            display_texts.append(text)
            self.cb_equipo.addItem(text, e.id)
            
        self.cb_equipo.setEditable(True)
        self.cb_equipo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        completer = QCompleter(display_texts)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        try: completer.setFilterMode(Qt.MatchFlag.MatchContains)
        except: pass
        self.cb_equipo.setCompleter(completer)
        
        if data and data.get("equipo_id"):
            idx = self.cb_equipo.findData(data["equipo_id"])
            if idx >= 0: self.cb_equipo.setCurrentIndex(idx)

        # Estado y Fecha
        self.cb_estado = QComboBox()
        self.cb_estado.addItems(["optimo", "defectuoso", "inoperativo"])
        if data and data.get("estado_equipo"):
            self.cb_estado.setCurrentText(data["estado_equipo"])
        
        self.ed_fecha = QDateEdit()
        self.ed_fecha.setCalendarPopup(True)
        self.ed_fecha.setDisplayFormat("dd/MM/yyyy")
        if data and data.get("fecha"):
            if hasattr(data["fecha"], 'year'):
                self.ed_fecha.setDate(QDate(data["fecha"].year, data["fecha"].month, data["fecha"].day))
            else:
                self.ed_fecha.setDate(QDate.fromString(str(data["fecha"]), "yyyy-MM-dd"))
        else:
            self.ed_fecha.setDate(QDate.currentDate())

        self.cb_equipo.currentIndexChanged.connect(self.on_equipo_changed)
        
        self.ed_desc = QTextEdit(data.get("descripcion", "") if data else "")
        self.ed_desc.setPlaceholderText("Detalle las acciones realizadas, repuestos utilizados, etc.")
        self.ed_desc.setFixedHeight(80)

        # --- Layout del Formulario ---
        
        # Fila 1: Equipo (Full width)
        col_eq = QVBoxLayout(); col_eq.setSpacing(6)
        col_eq.addWidget(QLabel("Equipo Afectado"))
        col_eq.addWidget(self.cb_equipo)
        card_layout.addLayout(col_eq)
        
        # Fila 2: Fecha y Estado Resultante
        row2 = QHBoxLayout(); row2.setSpacing(16)
        
        col_fecha = QVBoxLayout(); col_fecha.setSpacing(6)
        col_fecha.addWidget(QLabel("Fecha de Realización"))
        col_fecha.addWidget(self.ed_fecha)
        
        col_est = QVBoxLayout(); col_est.setSpacing(6)
        col_est.addWidget(QLabel("Estado Resultante del Equipo"))
        col_est.addWidget(self.cb_estado)
        
        row2.addLayout(col_fecha, 1)
        row2.addLayout(col_est, 1)
        card_layout.addLayout(row2)
        
        # Fila 3: Observaciones
        col_obs = QVBoxLayout(); col_obs.setSpacing(6)
        col_obs.addWidget(QLabel("Informe Técnico / Observaciones"))
        col_obs.addWidget(self.ed_desc)
        card_layout.addLayout(col_obs)

        card_layout.addSpacing(10)

        # Botones
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("class", "secondary")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("Registrar Mantenimiento")
        btn_save.setProperty("class", "primary")
        btn_save.clicked.connect(self.accept)
        
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        card_layout.addLayout(btn_row)
        
        layout.addWidget(card)

    def values(self) -> dict:
        return {
            "equipo_id": self.cb_equipo.currentData(),
            "fecha": self.ed_fecha.date().toString("yyyy-MM-dd"),
            "descripcion": self.ed_desc.toPlainText().strip(),
            "estado_equipo": self.cb_estado.currentText(),
        }

    def on_equipo_changed(self):
        equipo_id = self.cb_equipo.currentData()
        if equipo_id:
            equipo = next((e for e in list_equipos() if e.id == equipo_id), None)
            if equipo:
                self.cb_estado.setCurrentText(equipo.estado or "optimo")
        else:
            self.cb_estado.setCurrentText("optimo")


class RecordDetailDialog(QDialog):
    def __init__(self, title: str, fields: list[tuple[str, str]]):
        super().__init__()
        self.setWindowTitle(title)
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        lbl = QLabel(title)
        lbl.setProperty("role", "heading")
        layout.addWidget(lbl)
        
        card = QWidget()
        card.setProperty("class", "card")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(24, 24, 24, 24)
        c_layout.setSpacing(14)

        for label, value in fields:
            # Contenedor para cada par
            w = QWidget()
            wl = QVBoxLayout(w); wl.setContentsMargins(0,0,0,0); wl.setSpacing(4)
            
            title_lbl = QLabel(label)
            title_lbl.setStyleSheet("font-weight: 700; color: #94A3B8; font-size: 11px; text-transform: uppercase;")
            
            value_lbl = QLabel(value or "—")
            value_lbl.setStyleSheet("color: #E2E8F0; font-size: 14px;")
            value_lbl.setWordWrap(True)
            
            wl.addWidget(title_lbl)
            wl.addWidget(value_lbl)
            c_layout.addWidget(w)
            
        c_layout.addSpacing(10)
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_close = QPushButton("Cerrar")
        btn_close.setProperty("class", "primary")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        c_layout.addLayout(btn_row)

        layout.addWidget(card)

class GenerateDialog(QDialog):
    def __init__(self, mode: str):
        super().__init__()
        self.mode = mode
        self.setWindowTitle("Generar Reporte")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        lbl = QLabel(f"Reporte de {self.mode.capitalize()}")
        lbl.setProperty("role", "heading")
        layout.addWidget(lbl)

        card = QWidget()
        card.setProperty("class", "card")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(24, 24, 24, 24)
        c_layout.setSpacing(12)

        # Tipo de documento
        c_layout.addWidget(QLabel("Formato de Salida"))
        self.cb_type = QComboBox()
        self.cb_type.addItems(["PDF", "Word", "Excel"])
        c_layout.addWidget(self.cb_type)
        c_layout.addSpacing(8)

        # Filtros (Strategy Pattern via Report Forms)
        c_layout.addWidget(QLabel("Filtros Avanzados"))
        
        self.form_strategy = None
        if mode == 'equipos':
            self.form_strategy = EquiposReportForm()
        else:
            self.form_strategy = MantenimientosReportForm()
            
        c_layout.addWidget(self.form_strategy.get_widget())

        c_layout.addSpacing(16)
        
        # Botones
        btns = QHBoxLayout(); btns.addStretch(1)
        btn_ca = QPushButton("Cancelar")
        btn_ca.setProperty("class", "secondary")
        btn_ca.clicked.connect(self.reject)
        
        btn_ok = QPushButton("Generar")
        btn_ok.setProperty("class", "primary")
        btn_ok.clicked.connect(self.accept)
        
        btns.addWidget(btn_ca); btns.addWidget(btn_ok)
        c_layout.addLayout(btns)
        
        layout.addWidget(card)

    def values(self) -> dict:
        doc_type = self.cb_type.currentText()
        vals = self.form_strategy.get_values()
        vals['type'] = doc_type
        return vals

class UserEditDialog(QDialog):
    def __init__(self, user_obj, parent=None):
        super().__init__(parent)
        self.user_obj = user_obj
        self.setWindowTitle("Editar Usuario")
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        lbl_header = QLabel(f"Editar Usuario: {user_obj.username}")
        lbl_header.setProperty("role", "heading")
        layout.addWidget(lbl_header)
        
        card = QWidget()
        card.setProperty("class", "card")
        c = QVBoxLayout(card)
        c.setSpacing(12)
        
        self.user = QLineEdit(user_obj.username)
        self.user.setPlaceholderText("Usuario (login)")
        
        # Password
        from PyQt6.QtWidgets import QToolButton
        
        self.pwd = QLineEdit()
        self.pwd.setPlaceholderText("Nueva Contraseña (dejar vacío para mantener)")
        self.pwd.setEchoMode(QLineEdit.EchoMode.Password)
        
        pwd_row = QHBoxLayout()
        pwd_row.setSpacing(4)
        pwd_row.addWidget(self.pwd)
        self.btn_eye1 = QToolButton()
        self.btn_eye1.setText("👁")
        self.btn_eye1.setStyleSheet("QToolButton { border: none; background: transparent; font-size: 16px; }")
        self.btn_eye1.clicked.connect(lambda: self._toggle_pass(self.pwd, self.btn_eye1))
        pwd_row.addWidget(self.btn_eye1)
        
        c.addWidget(QLabel("Usuario")); c.addWidget(self.user)
        c.addWidget(QLabel("Contraseña")); c.addLayout(pwd_row)
        
        # Security Questions
        c.addSpacing(10)
        lbl_sec = QLabel("Preguntas de Seguridad")
        lbl_sec.setStyleSheet("font-weight: 600; color: #94A3B8; margin-top: 8px;")
        c.addWidget(lbl_sec)
        
        lbl_q1 = QLabel("¿Qué día y mes cumples años? (DD/MM)")
        lbl_q1.setStyleSheet("font-size: 12px; color: #E2E8F0;")
        self.sec_q1 = QLineEdit(user_obj.respuesta_seguridad_1 or "")
        c.addWidget(lbl_q1)
        c.addWidget(self.sec_q1)
        
        lbl_q2 = QLabel("Nombre de papá o mamá (en minúsculas)")
        lbl_q2.setStyleSheet("font-size: 12px; color: #E2E8F0;")
        self.sec_q2 = QLineEdit(user_obj.respuesta_seguridad_2 or "")
        c.addWidget(lbl_q2)
        c.addWidget(self.sec_q2)
        
        c.addSpacing(10)
        btn_row = QHBoxLayout(); btn_row.addStretch(1)
        btn_sav = QPushButton("Guardar"); btn_sav.setProperty("class", "primary")
        btn_can = QPushButton("Cancelar"); btn_can.setProperty("class", "secondary")
        
        btn_sav.clicked.connect(self.on_save)
        btn_can.clicked.connect(self.reject)
        
        btn_row.addWidget(btn_can); btn_row.addWidget(btn_sav)
        c.addLayout(btn_row)
        layout.addWidget(card)
    
    def _toggle_pass(self, field: QLineEdit, btn: QToolButton):
        if field.echoMode() == QLineEdit.EchoMode.Password:
            field.setEchoMode(QLineEdit.EchoMode.Normal)
            btn.setText("🔒")
        else:
            field.setEchoMode(QLineEdit.EchoMode.Password)
            btn.setText("👁")
        
    def on_save(self):
        u = self.user.text().strip()
        p = self.pwd.text()
        q1 = self.sec_q1.text().strip()
        q2 = self.sec_q2.text().strip().lower()
        
        if not u:
            QMessageBox.warning(self, "Error", "El usuario no puede estar vacío")
            return
            
        data = {}
        if u != self.user_obj.username:
            data['username'] = u
        
        if p:
            if not validate_password_strength(p):
                 QMessageBox.warning(self, "Seguridad", "La contraseña es muy débil (Mayús, núm, especial).")
                 return
            data['password'] = p
            
        if q1 != (self.user_obj.respuesta_seguridad_1 or ""):
            if not re.match(r"^\d{2}/\d{2}$", q1):
                 QMessageBox.warning(self, "Seguridad", "La fecha de cumpleaños debe tener el formato DD/MM (ej. 15/03).")
                 return
            data['respuesta_seguridad_1'] = q1
        if q2 != (self.user_obj.respuesta_seguridad_2 or ""):
            data['respuesta_seguridad_2'] = q2
            
        if not data:
            self.reject()
            return

        try:
            update_user_profile(self.user_obj.id, data)
            QMessageBox.information(self, "Éxito", "Usuario actualizado correctamente.")
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar: {e}")


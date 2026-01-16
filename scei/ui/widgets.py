import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QToolButton, QButtonGroup, QLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QDate, QRect, QPoint
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPainterPath, QColor

from ..utils import load_icon, load_pixmap, circular_pixmap

class PieChartWidget(QWidget):
    """Widget sencillo para gráficos circulares (pie) sin dependencias externas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[tuple[str, float, QColor]] = []
        self.setMinimumHeight(260)

    def set_data(self, items: list[tuple[str, float, QColor]]):
        """items: lista de (label, valor, color)."""
        self._data = [i for i in items if i[1] > 0]
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._data:
            return
        painter = QPainter(self)
        # Activar antialiasing para formas y texto (crucial para nitidez)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = self.rect().adjusted(10, 10, -10, -10)
        
        # Detectar modo de layout basado en el ancho disponible
        # Si es estrecho (como en las tarjetas del grid), poner leyenda abajo
        # Si es ancho (como en las gráficas superiores), poner leyenda a la derecha
        is_narrow = rect.width() < (rect.height() * 1.4)
        
        if is_narrow:
            # --- MODO VERTICAL (Leyenda Abajo) ---
            # Calcular altura necesaria para la leyenda
            legend_item_height = 24
            legend_height = len(self._data) * legend_item_height + 10
            
            # Área del gráfico
            chart_rect = rect.adjusted(0, 0, 0, -legend_height)
            
            # Área de leyenda
            legend_rect = rect.adjusted(0, chart_rect.height() + 10, 0, 0)
            
        else:
            # --- MODO HORIZONTAL (Leyenda Derecha) ---
            legend_width = 160
            chart_rect = rect.adjusted(0, 0, -legend_width, 0)
            legend_rect = rect.adjusted(chart_rect.width() + 10, 0, 0, 0)

        # Validación de seguridad
        if chart_rect.width() <= 0 or chart_rect.height() <= 0:
             return

        # --- DIBUJAR GRÁFICO ---
        # Maximizar radio
        size = min(chart_rect.width(), chart_rect.height())
        if size < 50: size = 50
        
        cx = chart_rect.center().x()
        cy = chart_rect.center().y()
        radius = (size // 2)
        
        # Agujero de la dona - 0.65 para equilibrar "aro grande" y espacio interior
        inner_radius = int(radius * 0.65)
        
        # Agujero fondo
        donut_hole = QPainterPath()
        donut_hole.addEllipse(cx - inner_radius, cy - inner_radius, inner_radius * 2, inner_radius * 2)

        total = sum(v for _, v, _ in self._data) or 1
        start_angle = 90 * 16

        from PyQt6.QtGui import QRadialGradient

        for label, value, color in self._data:
            if value <= 0: continue
            
            span = -360 * 16 * (value / total)
            
            path = QPainterPath()
            path.moveTo(cx, cy)
            path.arcTo(cx - radius, cy - radius, radius * 2, radius * 2, start_angle / 16, span / 16)
            path.closeSubpath()
            
            sector = path.subtracted(donut_hole)
            
            gradient = QRadialGradient(cx, cy, radius)
            gradient.setColorAt(0.5, color.darker(110))
            gradient.setColorAt(1.0, color)
            
            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(sector)
            
            # Borde fino
            painter.setPen(QColor("#0F172A"))
            painter.drawPath(sector)
            
            # Porcentaje si cabe
            percent = 100.0 * value / total
            # Solo si el radio es suficiente para que quede bien dentro del aro
            if percent >= 5 and radius > 35:
                # Posicionamiento en el medio del anillo
                mid_angle_rad = (start_angle + span / 2) / 16 * math.pi / 180.0
                label_radius = (radius + inner_radius) / 2
                tx = int(cx + label_radius * math.cos(mid_angle_rad))
                ty = int(cy - label_radius * math.sin(mid_angle_rad))
                
                font = painter.font()
                font.setBold(True)
                # Tamaño fuente dinámico leve
                fsize = 10 if radius > 60 else 8
                font.setPointSize(fsize)
                font.setFamily("Segoe UI") 
                painter.setFont(font)
                
                painter.setPen(QColor("#FFFFFF"))
                painter.drawText(tx - 30, ty - 8, 60, 16, Qt.AlignmentFlag.AlignCenter, f"{percent:.1f}%")

            start_angle += span

        # Texto Central (Total)
        painter.setPen(QColor("#E2E8F0"))
        font = painter.font()
        # Tamaño dinámico según tamaño del gráfico
        center_fsize = max(16, int(inner_radius * 0.7)) 
        font.setPointSize(center_fsize) 
        font.setBold(True)
        font.setFamily("Segoe UI")
        painter.setFont(font)
        
        # Calcular altura de texto
        total_cy = cy - (center_fsize // 3)
        painter.drawText(cx - 50, total_cy - (center_fsize), 100, center_fsize * 2, Qt.AlignmentFlag.AlignCenter, str(int(total)))
        
        font.setPointSize(max(9, int(center_fsize * 0.4)))
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor("#94A3B8"))
        painter.drawText(cx - 50, total_cy + (center_fsize // 2), 100, center_fsize, Qt.AlignmentFlag.AlignCenter, "Total")

        # --- DIBUJAR LEYENDA ---
        if is_narrow:
            # Centrada abajo
            ly = legend_rect.top()
            lx_start = legend_rect.center().x() - 60 # Ajuste aproximado para centrar visualmente bloques de texto
            
            for label, value, color in self._data:
                if value <= 0: continue
                
                # Centramos cada linea
                painter.setBrush(color)
                painter.setPen(Qt.PenStyle.NoPen)
                # Pequeño recuadro
                painter.drawRoundedRect(lx_start, ly + 4, 10, 10, 2, 2)
                
                painter.setPen(QColor("#CBD5E1"))
                font = painter.font()
                font.setPointSize(10)
                painter.setFont(font)
                painter.drawText(lx_start + 18, ly + 14, f"{label}: {int(value)}")
                
                ly += 22
        else:
            # A la derecha centrada verticalmente
            lx = legend_rect.left() + 10
            ly = rect.top() + (rect.height() - (len(self._data) * 28)) // 2
            
            for label, value, color in self._data:
                if value <= 0: continue
                
                painter.setBrush(color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(lx, ly + 4, 12, 12, 3, 3)
                
                painter.setPen(QColor("#CBD5E1"))
                font = painter.font()
                font.setPointSize(11)
                painter.setFont(font)
                painter.drawText(lx + 20, ly + 15, f"{label}: {int(value)}")
                
                ly += 30

class TopBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TopBarWidget")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(16)

        self.title = QLabel("Panel Principal")
        self.title.setProperty("role", "heading")
        layout.addWidget(self.title)

        layout.addStretch(1)

        self.avatar = QLabel()
        pix = load_pixmap("informatic_center.png")
        if pix.isNull():
            pix = QPixmap(48, 48)
            pix.fill(Qt.GlobalColor.transparent)
        self.avatar.setPixmap(pix.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(self.avatar)

    def set_title(self, title: str):
        self.title.setText(title)


class Sidebar(QWidget):
    navigation_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarWidget")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 20) # Reducido
        layout.setSpacing(12) # Reducido de 18

        # Branding crest + name
        brand_container = QWidget()
        brand_container.setObjectName("BrandContainer")
        brand_layout = QHBoxLayout(brand_container)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(10)

        self.logo_badge = QLabel()
        self.logo_badge.setObjectName("BrandBadge")
        badge_size = 50  # Reducido de 64 para ahorrar espacio vertical
        self.logo_badge.setFixedSize(badge_size, badge_size)
        self.logo_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_badge.setStyleSheet("background: transparent; border: none; padding: 0px;")

        crest_pix = load_pixmap("palavecino.png")
        if crest_pix.isNull():
            crest_pix = load_pixmap("palavecino_logo.png")
        if crest_pix.isNull():
            crest_pix = load_pixmap("logo_color.png")
        if crest_pix.isNull():
            self.logo_badge.setText("S")
        else:
            inner_size = max(32, badge_size - 6)
            circ = circular_pixmap(crest_pix, inner_size)
            if circ.isNull():
                self.logo_badge.setPixmap(crest_pix.scaled(inner_size, inner_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                self.logo_badge.setPixmap(circ)

        # Contenedor de Texto (Título + Subtítulo)
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 2, 0, 2)
        text_layout.setSpacing(1)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.brand_title = QLabel("SCEI")
        self.brand_title.setObjectName("BrandTitle")
        self.brand_title.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-size: 22px; 
            font-weight: 800;
            color: #F8FAFC;
            letter-spacing: 1px;
        """)
        
        self.brand_subtitle = QLabel("DIRECCIÓN DE INFORMÁTICA")
        self.brand_subtitle.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-size: 8px;
            font-weight: 600;
            color: #94A3B8;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        """)

        text_layout.addWidget(self.brand_title)
        text_layout.addWidget(self.brand_subtitle)

        brand_layout.addWidget(self.logo_badge)
        brand_layout.addWidget(text_container)
        brand_layout.addStretch(1)
        layout.addWidget(brand_container, 0, Qt.AlignmentFlag.AlignHCenter)

        layout.addSpacing(8)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        self.buttons = {}

        entries = [
            ("direcciones", "Inicio    ", "home.svg"),
            ("analitica", "Analítica", "analytics.svg"),
            ("bitacora", "Bitácora", "bitacora.svg"),
            ("configuracion", "Configuración", "settings.svg"),
        ]

        for key, text, icon in entries:
            btn = QToolButton()
            btn.setIcon(load_icon(icon))
            btn.setIconSize(QSize(18, 18))
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            btn.setText(text)
            btn.setCheckable(True)
            btn.setProperty("class", "sidebar-btn")
            layout.addWidget(btn)
            self.btn_group.addButton(btn)
            self.buttons[key] = btn
            btn.clicked.connect(lambda checked, k=key: checked and self.navigation_requested.emit(k))

        layout.addStretch(1)

        self.lock_graphic = QLabel()
        lock_pix = load_pixmap("seguridad.png")
        if not lock_pix.isNull():
            # Reducir imagen decorativa si la ventana es pequeña o quitar stretch
            self.lock_graphic.setPixmap(lock_pix.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.lock_graphic.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.lock_graphic)

        self.btn_logout = QPushButton("Cerrar sesión")
        self.btn_logout.setObjectName("SidebarLogout")
        layout.addWidget(self.btn_logout)

    def select(self, key: str):
        if key in self.buttons:
            self.buttons[key].setChecked(True)

    def clear_selection(self):
        # Permitir dejar todos los botones sin selección
        self.btn_group.setExclusive(False)
        for btn in self.buttons.values():
            btn.setChecked(False)
            btn.clearFocus()
        self.btn_group.setExclusive(True)


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def doLayout(self, rect, testOnly):
        if not self.itemList:
            return 0
            
        x = rect.x()
        y = rect.y()
        spacing = self.spacing()
        if spacing == -1: spacing = 10

        # Calcular ancho base basado en el mínimo de los items (asumiendo homogeneidad)
        # Usamos el primer item o el maximo de los minimos para seguridad
        min_item_w = 0
        for item in self.itemList:
            w = item.minimumSize().width()
            # Si no hay minSize definido (0), usamos sizeHint
            if w <= 0: w = item.sizeHint().width()
            if w > min_item_w: min_item_w = w
        
        if min_item_w <= 0: min_item_w = 100 # Fallback

        available_w = rect.width()
        
        # Calcular columnas (N)
        # Formula: N * w + (N-1) * s <= available
        # N * (w + s) <= available + s
        n_cols = int((available_w + spacing) / (min_item_w + spacing))
        if n_cols < 1: n_cols = 1
        
        # Calcular ancho exacto de celda para llenar el espacio
        # avail = N * cell_w + (N-1) * s
        # cell_w = (avail - (N-1)*s) / N
        total_spacing = (n_cols - 1) * spacing
        cell_w = int((available_w - total_spacing) / n_cols)
        
        # Layout
        col = 0
        row_h = 0
        start_y = y
        
        for item in self.itemList:
            h = item.sizeHint().height()
            if h < item.minimumSize().height(): h = item.minimumSize().height()
            
            if not testOnly:
                item.setGeometry(QRect(x, y, cell_w, h))
            
            row_h = max(row_h, h)
            
            x += cell_w + spacing
            col += 1
            
            if col >= n_cols:
                col = 0
                x = rect.x()
                y += row_h + spacing
                row_h = 0
                
        # Altura final
        total_h = y - rect.y()
        if col > 0:
            total_h += row_h
        else:
            # Si terminamos justo al final de una fila, el loop agregó spacing extra
            total_h -= spacing
            
        return total_h

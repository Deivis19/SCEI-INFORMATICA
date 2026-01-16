
from collections import defaultdict
from datetime import date
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QScrollArea, QGridLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from ..widgets import PieChartWidget, FlowLayout
from ...data.repositories import list_equipos, list_mantenimientos, list_direcciones
from ...data.models import Mantenimiento
from ...config import DIRECCIONES_HIERARCHY

class AnaliticaTab(QWidget):
    open_direccion = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 20, 10, 20) # Reducir márgenes laterales
        layout.setSpacing(20)

        # Header
        header_lbl = QLabel("Analítica General")
        header_lbl.setStyleSheet("font-size: 24px; font-weight: 700; color: #F8FAFC; margin-bottom: 8px;")
        layout.addWidget(header_lbl)

        # Sección de Gráficas
        charts_row = QHBoxLayout()
        charts_row.setSpacing(20)

        # -- Gráfica 1: Estados --
        card1 = QWidget()
        card1.setProperty("class", "card")
        c1_layout = QVBoxLayout(card1)
        c1_layout.setContentsMargins(24, 20, 24, 24)
        c1_layout.setSpacing(16)
        
        lbl1 = QLabel("Distribución de Estados")
        lbl1.setStyleSheet("font-size: 16px; font-weight: 600; color: #E2E8F0;")
        lbl1.setAlignment(Qt.AlignmentFlag.AlignLeft)
        c1_layout.addWidget(lbl1)
        
        self.pie_equipos = PieChartWidget()
        c1_layout.addWidget(self.pie_equipos)
        charts_row.addWidget(card1, 1)

        # -- Gráfica 2: Mejoras --
        card2 = QWidget()
        card2.setProperty("class", "card")
        c2_layout = QVBoxLayout(card2)
        c2_layout.setContentsMargins(24, 20, 24, 24)
        c2_layout.setSpacing(16)
        
        lbl2 = QLabel("Evolución de Mantenimientos")
        lbl2.setStyleSheet("font-size: 16px; font-weight: 600; color: #E2E8F0;")
        lbl2.setAlignment(Qt.AlignmentFlag.AlignLeft)
        c2_layout.addWidget(lbl2)
        
        self.pie_mejoras = PieChartWidget()
        c2_layout.addWidget(self.pie_mejoras)
        charts_row.addWidget(card2, 1)

        layout.addLayout(charts_row)
        
        # --- Sección: Por Direcciones ---
        layout.addSpacing(20)
        lbl_dirs = QLabel("Estado por Direcciones")
        lbl_dirs.setStyleSheet("font-size: 18px; font-weight: 700; color: #F8FAFC; margin-top: 10px; margin-bottom: 8px;")
        layout.addWidget(lbl_dirs)
        
        layout.addWidget(lbl_dirs)
        
        # Container para FlowLayout
        self.flow_container = QWidget()
        self.flow_layout = FlowLayout(self.flow_container)
        self.flow_layout.setSpacing(12) # Reducir espacio entre tarjetas
        self.flow_layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.flow_container)

        layout.addStretch(1)
        
        scroll.setWidget(container)
        root = QVBoxLayout(self)
        root.setContentsMargins(0,0,0,0)
        root.addWidget(scroll)

        self.refresh()

    def refresh(self):
        # --- Equipos por estado (global) ---
        total_opt = total_def = total_inop = 0
        equipos = list_equipos()
        total_equipos = len(equipos) or 1
        
        for e in equipos:
            estado = (e.estado or "optimo").lower()
            if estado == "defectuoso":
                total_def += 1
            elif estado == "inoperativo":
                total_inop += 1
            else:
                total_opt += 1
        
        self.pie_equipos.set_data([
            ("Óptimos", total_opt, QColor("#22C55E")),
            ("Defectuosos", total_def, QColor("#F97316")),
            ("Inoperativos", total_inop, QColor("#EF4444")),
        ])

        # --- Mejoras de estado (Lógica Original) ---
        mejoras = 0
        agravado = 0
        mant_por_equipo: dict[int, list[Mantenimiento]] = defaultdict(list)
        for m in list_mantenimientos():
            if m.equipo_id is not None:
                mant_por_equipo[m.equipo_id].append(m)

        rank = {"optimo": 2, "defectuoso": 1, "inoperativo": 0}

        for eq in equipos:
            registros = mant_por_equipo.get(eq.id, [])
            if not registros:
                continue
            registros.sort(key=lambda m: m.fecha or date.today())

            estados = [(m.estado_equipo or "").lower() for m in registros if (m.estado_equipo or "").strip()]
            if not estados:
                continue
            
            first_state = estados[0] if estados[0] in rank else "optimo"
            last_state = estados[-1] if estados[-1] in rank else first_state

            prev_estado: str | None = None
            mejoro = False
            empeoro = False
            had_optimo = False
            had_worse = False
            last_improve_date: date | None = None
            
            for m, est in zip(registros, estados):
                est_norm = est if est in rank else "optimo"
                if est_norm == "optimo":
                    had_optimo = True
                if est_norm in {"defectuoso", "inoperativo"}:
                    had_worse = True

                if prev_estado is not None:
                    if prev_estado in {"defectuoso", "inoperativo"} and est_norm == "optimo":
                        mejoro = True
                        last_improve_date = m.fecha or date.today()
                    if prev_estado == "optimo" and est_norm in {"defectuoso", "inoperativo"}:
                        empeoro = True
                prev_estado = est_norm

            recent_improve = False
            if mejoro and last_improve_date is not None:
                days_since = (date.today() - last_improve_date).days
                if days_since <= 14:
                    recent_improve = True

            if recent_improve:
                mejoras += 1
            else:
                if (
                    rank.get(last_state, 2) < rank.get(first_state, 2)
                    or empeoro
                    or (had_worse and not had_optimo)
                ):
                    agravado += 1

        # Cálculo original: Sin cambios es el resto del universo de equipos
        sin_cambios = max(total_equipos - mejoras - agravado, 0)
        
        self.pie_mejoras.set_data([
            ("Mejoraron", mejoras, QColor("#38BDF8")),    # Sky 400
            ("Sin cambios", sin_cambios, QColor("#22C55E")), # Green Original
            ("Agravado", agravado, QColor("#EF4444")),    # Red Original
        ])
        
        self.refresh_direcciones(equipos)

    def refresh_direcciones(self, all_equipos):
        # Limpiar layout
        # Para FlowLayout, mejor borrar items uno a uno
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Agrupar equipos por direccion
        eq_by_dir = defaultdict(list)
        for e in all_equipos:
            if e.direccion_id:
                eq_by_dir[e.direccion_id].append(e)
                
        # Obtener y ordenar direcciones
        dirs = list_direcciones()
        pos_map = {name: i for i, name in enumerate(DIRECCIONES_HIERARCHY)}
        dirs.sort(key=lambda d: (pos_map.get(d.nombre or "", 10000), (d.nombre or "").lower()))
        
        for d in dirs:
            my_eqs = eq_by_dir.get(d.id, [])
            if not my_eqs:
                continue
                
            # Calcular estados
            c_opt = c_def = c_inop = 0
            for e in my_eqs:
                st = (e.estado or "optimo").lower()
                if st == "defectuoso": c_def += 1
                elif st == "inoperativo": c_inop += 1
                else: c_opt += 1
            
            # Crear Card
            card = QWidget()
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.setProperty("class", "card")
            # Usar MinimumSize en lugar de FixedSize para permitir expansión
            # El FlowLayout modificado se encargará de "Expandir" hasta llenar la fila
            card.setMinimumSize(220, 290)
            
            # Navegacion al hacer click
            card.mouseReleaseEvent = lambda e, did=d.id: self.open_direccion.emit(did)
            
            cv = QVBoxLayout(card)
            cv.setContentsMargins(16, 16, 16, 16)
            
            # Titulo Card
            l_name = QLabel(d.nombre)
            l_name.setWordWrap(True)
            # Limitar a 2-3 líneas y elipsis si es necesario (manejado por wordwrap y tamaño fijo)
            l_name.setStyleSheet("font-size: 13px; font-weight: 700; color: #E2E8F0; margin-bottom: 4px;")
            l_name.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
            # Fijar altura del título para evitar saltos de layout
            l_name.setFixedHeight(45) 
            cv.addWidget(l_name)
            
            # Mini Chart
            pie = PieChartWidget()
            pie.set_data([
                ("Óptimos", c_opt, QColor("#22C55E")),
                ("Defectuosos", c_def, QColor("#F97316")),
                ("Inoperativos", c_inop, QColor("#EF4444")),
            ])
            cv.addWidget(pie)
            
            self.flow_layout.addWidget(card)

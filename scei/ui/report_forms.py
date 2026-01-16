from abc import ABC, abstractmethod
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, QCheckBox, QDateEdit
)
from PyQt6.QtCore import QDate

class IReportForm(ABC):
    """Interfaz abstracta para formularios de recorte (SOLID: OCP/LSP)."""
    @abstractmethod
    def get_widget(self) -> QWidget:
        """Devuelve el widget configurado."""
        pass

    @abstractmethod
    def get_values(self) -> dict:
        """Devuelve los valores del formulario."""
        pass

class BaseReportForm(IReportForm):
    def __init__(self):
        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
    def get_widget(self) -> QWidget:
        return self.widget

class EquiposReportForm(BaseReportForm):
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        grid = QGridLayout()
        grid.setSpacing(8)
        
        self.ed_codigo = QLineEdit(); self.ed_codigo.setPlaceholderText("Código...")
        self.ed_marca = QLineEdit(); self.ed_marca.setPlaceholderText("Marca...")
        self.ed_modelo = QLineEdit(); self.ed_modelo.setPlaceholderText("Modelo...")
        self.ed_serie = QLineEdit(); self.ed_serie.setPlaceholderText("Serie...")
        self.ed_desc = QLineEdit(); self.ed_desc.setPlaceholderText("Descripción...")
        self.cb_estado = QComboBox(); self.cb_estado.addItem("(Todos)", "")
        self.cb_estado.addItems(["optimo", "defectuoso", "inoperativo"])
        
        grid.addWidget(QLabel("Código:"), 0, 0); grid.addWidget(self.ed_codigo, 0, 1)
        grid.addWidget(QLabel("Marca:"), 0, 2); grid.addWidget(self.ed_marca, 0, 3)
        grid.addWidget(QLabel("Modelo:"), 1, 0); grid.addWidget(self.ed_modelo, 1, 1)
        grid.addWidget(QLabel("Serie:"), 1, 2); grid.addWidget(self.ed_serie, 1, 3)
        
        self.layout.addLayout(grid)
        self.layout.addWidget(QLabel("Descripción:"))
        self.layout.addWidget(self.ed_desc)
        self.layout.addWidget(QLabel("Estado:"))
        self.layout.addWidget(self.cb_estado)

    def get_values(self) -> dict:
        return {
            "codigo": self.ed_codigo.text().strip(),
            "descripcion": self.ed_desc.text().strip(),
            "marca": self.ed_marca.text().strip(),
            "modelo": self.ed_modelo.text().strip(),
            "serie": self.ed_serie.text().strip(),
            "estado": self.cb_estado.currentText() if self.cb_estado.currentData() is None else self.cb_estado.currentData(),
        }

class MantenimientosReportForm(BaseReportForm):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        grid = QGridLayout()
        self.de_from = QDateEdit(); self.de_from.setCalendarPopup(True)
        self.de_to = QDateEdit(); self.de_to.setCalendarPopup(True)
        self.de_from.setDate(QDate.currentDate().addMonths(-1))
        self.de_to.setDate(QDate.currentDate())
        
        self.cb_from_enabled = QCheckBox("Desde")
        self.cb_to_enabled = QCheckBox("Hasta")
        self.cb_from_enabled.setChecked(True); self.cb_to_enabled.setChecked(True)
        
        self.cb_from_enabled.toggled.connect(self.de_from.setEnabled)
        self.cb_to_enabled.toggled.connect(self.de_to.setEnabled)
        
        grid.addWidget(self.cb_from_enabled, 0, 0); grid.addWidget(self.de_from, 0, 1)
        grid.addWidget(self.cb_to_enabled, 0, 2); grid.addWidget(self.de_to, 0, 3)
        self.layout.addLayout(grid)
        
        self.cb_estado = QComboBox(); self.cb_estado.addItem("(Todos)", "")
        self.cb_estado.addItems(["optimo", "defectuoso", "inoperativo"])
        self.ed_equipo = QLineEdit(); self.ed_equipo.setPlaceholderText("Código, marca, modelo...")
        self.ed_obs = QLineEdit(); self.ed_obs.setPlaceholderText("Texto en observación...")
        
        self.layout.addWidget(QLabel("Estado resultante:"))
        self.layout.addWidget(self.cb_estado)
        self.layout.addWidget(QLabel("Equipo asociado:"))
        self.layout.addWidget(self.ed_equipo)
        self.layout.addWidget(QLabel("Observación:"))
        self.layout.addWidget(self.ed_obs)

    def get_values(self) -> dict:
        return {
            "from": self.de_from.date().toString("yyyy-MM-dd") if self.cb_from_enabled.isChecked() else "",
            "to": self.de_to.date().toString("yyyy-MM-dd") if self.cb_to_enabled.isChecked() else "",
            "estado": self.cb_estado.currentText() if self.cb_estado.currentData() is None else self.cb_estado.currentData(),
            "equipo": self.ed_equipo.text().strip(),
            "obs": self.ed_obs.text().strip(),
        }

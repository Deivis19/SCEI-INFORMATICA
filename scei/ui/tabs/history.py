
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QDesktopServices, QUrl

from ...utils import load_icon
from ...logger import LOGS_FILE

# Archivo de historial junto al de logs
HISTORY_FILE = os.path.join(os.path.dirname(LOGS_FILE) if LOGS_FILE else os.path.dirname(os.path.abspath(__file__)), "pdf_logs.json")

class PdfRegistrosTab(QWidget):
    def __init__(self):
        super().__init__()
        self.registros = []
        self.load_history()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        lbl = QLabel("Historial de Documentos Generados")
        lbl.setProperty("role", "heading")
        header.addWidget(lbl)
        header.addStretch(1)
        
        btn_clear = QPushButton("Limpiar Historial")
        btn_clear.clicked.connect(self.clear_history)
        header.addWidget(btn_clear)

        btn_refresh = QPushButton("Refrescar")
        btn_refresh.clicked.connect(self.refresh_table)
        header.addWidget(btn_refresh)
        
        layout.addLayout(header)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Fecha", "Archivo", "Acción"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # Timer para auto-recarga (opcional, lo dejamos manual o al mostrar)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_new_files)
        # self.timer.start(5000) 
        self.refresh_table()

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.registros = json.load(f)
            except:
                self.registros = []
        else:
            self.registros = []

    def save_history(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.registros, f, ensure_ascii=False, indent=4)
        except:
            pass

    def add_record(self, filepath):
        # Esta función puede ser llamada desde otros módulos si se desea centralizar
        rec = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "archivo": filepath
        }
        self.registros.insert(0, rec)
        self.save_history()
        self.refresh_table()

    def refresh_table(self):
        self.load_history()
        self.table.setRowCount(0)
        for i, reg in enumerate(self.registros):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(reg.get("fecha", "")))
            
            path_item = QTableWidgetItem(reg.get("archivo", ""))
            path_item.setToolTip(reg.get("archivo", ""))
            self.table.setItem(row, 1, path_item)

            btn = QPushButton("Abrir")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # Usar lambda con valor default para capturar el path actual
            btn.clicked.connect(lambda _, p=reg.get("archivo", ""): self.open_file(p))
            self.table.setCellWidget(row, 2, btn)

    def open_file(self, path):
        if os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            QMessageBox.warning(self, "Error", f"El archivo ya no existe:\n{path}")

    def clear_history(self):
        if QMessageBox.question(self, "Limpiar", "¿Borrar todo el historial?") == QMessageBox.StandardButton.Yes:
            self.registros = []
            self.save_history()
            self.refresh_table()

    def check_new_files(self):
        # Lógica para detectar nuevos archivos externos si fuera necesario
        pass

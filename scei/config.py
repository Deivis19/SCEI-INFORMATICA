
# Configuración global de la aplicación

VALID_USERS = ["DI-ADMIN"]
BITACORA_CLEAN_INTERVAL_DAYS = 30

import sys
import os
import shutil
from pathlib import Path

DB_NAME = "scei.db"

# Lógica de detección de entorno y autodespliegue de BD
if getattr(sys, 'frozen', False):
    # Estamos en el ejecutable .exe
    # 1. Definir ruta persistente en AppData del usuario
    app_data = Path(os.getenv('LOCALAPPDATA', os.path.expanduser('~'))) / "SCEI"
    app_data.mkdir(parents=True, exist_ok=True)
    
    target_db = app_data / DB_NAME
    
    # 2. Si no existe la BD en AppData, copiarla desde el paquete interno (bundled)
    if not target_db.exists():
        try:
            # sys._MEIPASS es donde PyInstaller descomprime los archivos temporales
            bundled_db = Path(sys._MEIPASS) / DB_NAME # type: ignore
            if bundled_db.exists():
                shutil.copy2(bundled_db, target_db)
        except Exception as e:
            # Fallback o log silencioso si falla la copia inicial
            pass
            
    DATABASE_URL = f"sqlite:///{target_db}"
else:
    # Modo desarrollo: usar BD en la raíz del proyecto
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATABASE_URL = f"sqlite:///{BASE_DIR / DB_NAME}"

# Orden jerárquico de Direcciones para la vista de Inicio
DIRECCIONES_HIERARCHY = [
    "Presidencia",
    "Vicepresidencia",
    "Secretaría",
    "Auditoría Interna",
    "Dirección de Comunicación y Participación Ciudadana",
    "Dirección de Legislación",
    "Dirección de Administración",
    "Coordinación de Bienes",
    "Coordinación de Compras",
    "Dirección de Informática",
    "Dirección de Gestión Humana",
    "Coordinación de Servicios Generales",
    "División de Seguridad Industrial",
]

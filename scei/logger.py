import os
import sys
import json
from datetime import datetime

# Variables globales de estado para logs
LOGS: list[dict] = []
LOGS_FILE = ""

def _resolve_logs_path() -> str:
    # Logs portables: si está congelado, usar AppData para evitar ensuciar carpeta del exe
    try:
        if getattr(sys, "frozen", False):
            base_user = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or os.path.expanduser("~")
            app_dir = os.path.join(base_user, "SCEI")
            os.makedirs(app_dir, exist_ok=True)
            return os.path.join(app_dir, "logs.json")
    except Exception:
        pass
    # Desarrollo: archivo local del proyecto (subir un nivel desde 'scei' o mantener en raíz)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(BASE_DIR), "logs.json")

def init_logger():
    global LOGS_FILE
    LOGS_FILE = _resolve_logs_path()
    load_logs()

def load_logs():
    global LOGS
    if not LOGS_FILE:
        return
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                LOGS.clear()
                for log in data:
                    if isinstance(log, dict):
                        log['date'] = datetime.fromisoformat(log['date']) if isinstance(log['date'], str) else log['date']
                        if 'user' in log:
                            del log['user']
                        if 'direccion' not in log:
                            log['direccion'] = ""
                        LOGS.append(log)
                    else:
                        # Handle old format if any
                        LOGS.append({
                            "date": datetime.now(),
                            "action": str(log),
                            "desc": "",
                            "direccion": ""
                        })
        except:
            LOGS.clear()
    else:
        LOGS.clear()
    # Save updated logs in normalized format
    save_logs()

def save_logs():
    if not LOGS_FILE:
        return
    try:
        with open(LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(LOGS, f, ensure_ascii=False, indent=4, default=str)
    except:
        pass

def add_log(action: str, desc: str, direccion: str | None = None):
    log_entry = {
        "date": datetime.now(),
        "action": action,
        "desc": desc,
        "direccion": direccion or ""
    }
    LOGS.insert(0, log_entry)
    save_logs()

# Inicializar ruta al cargar módulo
LOGS_FILE = _resolve_logs_path()

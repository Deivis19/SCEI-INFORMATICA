"""
Este módulo actúa ahora como una fachada (Facade/Adapter) para mantener compatibilidad
con el código existente mientras se transiciona a una arquitectura basada en Repositorios (SOLID).
"""
from typing import Iterable
from .models import Direccion, Equipo, Mantenimiento
from .. import session # Access global session for current user
from .sql_repositories import (
    SQLDireccionRepository,
    SQLEquipoRepository,
    SQLMantenimientoRepository,
    SQLUserRepository,
    SQLBitacoraRepository,
    session_scope
)

# Instancias globales de los repositorios
# En un sistema con inyección de dependencias, esto se manejaría en un contenedor (Container).
_direccion_repo = SQLDireccionRepository()
_equipo_repo = SQLEquipoRepository()
_mantenimiento_repo = SQLMantenimientoRepository()
_user_repo = SQLUserRepository()
_user_repo = SQLUserRepository()
_bitacora_repo = SQLBitacoraRepository()

def _log_action(action: str, desc: str, modulo: str):
    """Helper to log actions automatically with current user."""
    try:
        user_id = None
        if session.CURRENT_USER:
            u = _user_repo.get_by_username(session.CURRENT_USER)
            if u: user_id = u.id
        _bitacora_repo.add_log(user_id, action, desc, modulo)
    except Exception:
        pass # Logging should not break business logic


# --- Direcciones ---
def list_direcciones() -> list[Direccion]:
    return _direccion_repo.list_all()

def add_direccion(nombre: str) -> None:
    _direccion_repo.add(nombre)

def update_direccion(id_: int, nombre: str, activo: int) -> None:
    _direccion_repo.update(id_, nombre, activo)

def delete_direccion(id_: int) -> None:
    _direccion_repo.delete(id_)

# --- Equipos ---
def list_equipos() -> list[Equipo]:
    return _equipo_repo.list_all()

def list_equipos_by_direccion(direccion_id: int | None = None) -> list[Equipo]:
    return _equipo_repo.list_by_direccion(direccion_id)

def add_equipo(data: dict) -> None:
    _equipo_repo.add(data)

def update_equipo(id_: int, data: dict) -> None:
    _equipo_repo.update(id_, data)

def get_equipo(id_: int):
    return _equipo_repo.get(id_)

def delete_equipo(id_: int) -> None:
    _equipo_repo.delete(id_)

# --- Mantenimientos ---
def list_mantenimientos() -> list[Mantenimiento]:
    return _mantenimiento_repo.list_all()

def list_mantenimientos_by_direccion(direccion_id: int) -> list[Mantenimiento]:
    return _mantenimiento_repo.list_by_direccion(direccion_id)

def add_mantenimiento(vals: dict):
    m = _mantenimiento_repo.add(vals)
    return m

def update_mantenimiento(id_: int, data: dict) -> None:
    _mantenimiento_repo.update(id_, data)

def delete_mantenimiento(id_: int) -> None:
    _mantenimiento_repo.delete(id_)

def get_mantenimiento(id_: int):
    return _mantenimiento_repo.get(id_)

# --- Usuarios ---
def check_user(username: str, password: str) -> bool:
    return _user_repo.check_credentials(username, password)

def set_user_password(username: str, password: str) -> bool:
    return _user_repo.set_password(username, password)

def create_user(data: dict):
    return _user_repo.create_user(data)

def get_user(username: str):
    return _user_repo.get_by_username(username)

def list_users() -> list:
    return [u.username for u in _user_repo.list_all()]

def list_users_full():
    """Returns list of User objects instead of just strings"""
    return _user_repo.list_all()

def delete_user(user_id: int) -> bool:
    return _user_repo.delete_user(user_id)

def update_user_profile(user_id: int, data: dict) -> bool:
    return _user_repo.update_user(user_id, data)

# --- Bitacora ---
def add_bitacora_log(usuario_id: int | None, action: str, desc: str, modulo: str) -> None:
    _bitacora_repo.add_log(usuario_id, action, desc, modulo)

def list_bitacora_entries(limit: int = 50) -> list:
    return _bitacora_repo.list_recent(limit)

from abc import ABC, abstractmethod
from typing import List, Optional, Protocol, Any
from datetime import date
from .models import Direccion, Equipo, Mantenimiento, User, Bitacora

# Usamos Protocol o ABC para definir las interfaces

class IDireccionRepository(ABC):
    @abstractmethod
    def list_all(self) -> List[Direccion]: ...
    
    @abstractmethod
    def add(self, nombre: str) -> None: ...
    
    @abstractmethod
    def update(self, id_: int, nombre: str, activo: int) -> None: ...
    
    @abstractmethod
    def delete(self, id_: int) -> None: ...

class IEquipoRepository(ABC):
    @abstractmethod
    def list_all(self) -> List[Equipo]: ...
    
    @abstractmethod
    def list_by_direccion(self, direccion_id: int | None = None) -> List[Equipo]: ...
    
    @abstractmethod
    def add(self, data: dict) -> None: ...
    
    @abstractmethod
    def update(self, id_: int, data: dict) -> None: ...
    
    @abstractmethod
    def get(self, id_: int) -> Optional[Equipo]: ...
    
    @abstractmethod
    def delete(self, id_: int) -> None: ...

class IMantenimientoRepository(ABC):
    @abstractmethod
    def list_all(self) -> List[Mantenimiento]: ...
    
    @abstractmethod
    def list_by_direccion(self, direccion_id: int) -> List[Mantenimiento]: ...
    
    @abstractmethod
    def add(self, vals: dict) -> Mantenimiento: ...
    
    @abstractmethod
    def update(self, id_: int, data: dict) -> None: ...
    
    @abstractmethod
    def delete(self, id_: int) -> None: ...
    
    @abstractmethod
    def get(self, id_: int) -> Optional[Mantenimiento]: ...

class IUserRepository(ABC):
    @abstractmethod
    def check_credentials(self, username: str, password: str) -> bool: ...
    
    @abstractmethod
    def set_password(self, username: str, password: str) -> bool: ...

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]: ...
    
    @abstractmethod
    def create_user(self, data: dict) -> User: ...

    @abstractmethod
    def list_all(self) -> List[User]: ...

class IBitacoraRepository(ABC):
    @abstractmethod
    def add_log(self, usuario_id: int | None, action: str, desc: str, modulo: str) -> None: ...
    
    @abstractmethod
    def list_recent(self, limit: int = 50) -> List[Bitacora]: ...

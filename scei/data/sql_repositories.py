from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from .db import SessionLocal
from .models import Direccion, Equipo, Mantenimiento, User, Bitacora
from .interfaces import (
    IDireccionRepository,
    IEquipoRepository,
    IMantenimientoRepository,
    IUserRepository,
    IBitacoraRepository
)
from contextlib import contextmanager

# Helper context manager (kept as utility)
@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

class SQLDireccionRepository(IDireccionRepository):
    def list_all(self) -> list[Direccion]:
        with session_scope() as s:
            return list(s.scalars(select(Direccion).order_by(Direccion.nombre)))

    def add(self, nombre: str) -> None:
        with session_scope() as s:
            s.add(Direccion(nombre=nombre, activo=1))

    def update(self, id_: int, nombre: str, activo: int) -> None:
        with session_scope() as s:
            d = s.get(Direccion, id_)
            if not d:
                return
            d.nombre = nombre
            d.activo = activo

    def delete(self, id_: int) -> None:
        with session_scope() as s:
            d = s.get(Direccion, id_)
            if d:
                s.delete(d)

class SQLEquipoRepository(IEquipoRepository):
    def list_all(self) -> list[Equipo]:
        with session_scope() as s:
            return list(s.scalars(select(Equipo).order_by(Equipo.id.desc())))

    def list_by_direccion(self, direccion_id: int | None = None) -> list[Equipo]:
        with session_scope() as s:
            query = s.query(Equipo).options(selectinload(Equipo.mantenimientos))
            if direccion_id:
                query = query.filter_by(direccion_id=direccion_id)
            return query.order_by(Equipo.id.desc()).all()

    def add(self, data: dict) -> None:
        with session_scope() as s:
            s.add(Equipo(**data))

    def update(self, id_: int, data: dict) -> None:
        with session_scope() as s:
            e = s.get(Equipo, id_)
            if not e:
                return
            for k, v in data.items():
                setattr(e, k, v)

    def get(self, id_: int):
        with session_scope() as s:
            return s.get(Equipo, id_)

    def delete(self, id_: int) -> None:
        with session_scope() as s:
            e = s.get(Equipo, id_)
            if e:
                # Eliminar primero los mantenimientos asociados a este equipo
                # para respetar la restricción NOT NULL de mantenimiento.equipo_id
                s.query(Mantenimiento).filter_by(equipo_id=id_).delete()
                s.delete(e)

class SQLMantenimientoRepository(IMantenimientoRepository):
    def list_all(self) -> list[Mantenimiento]:
        with session_scope() as s:
            return s.query(Mantenimiento).options(selectinload(Mantenimiento.equipo)).all()

    def list_by_direccion(self, direccion_id: int) -> list[Mantenimiento]:
        with session_scope() as s:
            return s.query(Mantenimiento).join(Equipo, Mantenimiento.equipo_id == Equipo.id)\
                .filter(Equipo.direccion_id == direccion_id)\
                .options(selectinload(Mantenimiento.equipo)).all()

    def add(self, vals: dict):
        with session_scope() as s:
            if isinstance(vals.get('fecha'), str):
                 vals['fecha'] = date.fromisoformat(vals['fecha'])
            
            # Clean dict of keys not in model if necessary
            valid_keys = Mantenimiento.__table__.columns.keys()
            filtered_vals = {k: v for k, v in vals.items() if k in valid_keys}
            
            m = Mantenimiento(**filtered_vals)
            s.add(m)
            s.commit()
            # Refresh to get ID if needed, but we return object.
            # Note: The object is detached after session close.
            return m

    def update(self, id_: int, data: dict) -> None:
        with session_scope() as s:
            m = s.get(Mantenimiento, id_)
            if not m:
                return
            for k, v in data.items():
                if k == 'fecha' and isinstance(v, str):
                    setattr(m, k, date.fromisoformat(v))
                else:
                    setattr(m, k, v)

    def delete(self, id_: int) -> None:
        with session_scope() as s:
            m = s.get(Mantenimiento, id_)
            if m:
                s.delete(m)

    def get(self, id_: int):
        with session_scope() as s:
            return s.query(Mantenimiento).options(selectinload(Mantenimiento.equipo)).filter_by(id=id_).first()

class SQLUserRepository(IUserRepository):
    def check_credentials(self, username: str, password: str) -> bool:
        with session_scope() as s:
            return s.query(User).filter_by(username=username, password=password).first() is not None

    def set_password(self, username: str, password: str) -> bool:
        with session_scope() as s:
            user = s.query(User).filter_by(username=username).first()
            if not user:
                return False
            user.password = password
            return True

    def get_by_username(self, username: str) -> User | None:
        with session_scope() as s:
            # detach to use outside scope? or just fields. 
            # ideally repo returns DTOs or detached objects. 
            u = s.query(User).filter_by(username=username).first()
            if u:
                s.refresh(u)
                s.expunge(u)
            return u

    def create_user(self, data: dict) -> User:
        with session_scope() as s:
            # Validate unique?
            if s.query(User).filter_by(username=data['username']).first():
                raise ValueError("El usuario ya existe")
            u = User(**data)
            s.add(u)
            s.commit()
            s.refresh(u)
            s.expunge(u)
            return u

    def list_all(self) -> list[User]:
        with session_scope() as s:
            return list(s.scalars(select(User).order_by(User.username)))

    def delete_user(self, user_id: int) -> bool:
        with session_scope() as s:
            u = s.get(User, user_id)
            if u:
                s.delete(u)
                return True
            return False

    def update_user(self, user_id: int, data: dict) -> bool:
        with session_scope() as s:
            u = s.get(User, user_id)
            if not u:
                return False
            # Check unique username if changing
            if 'username' in data and data['username'] != u.username:
                if s.query(User).filter_by(username=data['username']).first():
                     raise ValueError("El nombre de usuario ya está en uso")
            for k, v in data.items():
                setattr(u, k, v)
            return True

class SQLBitacoraRepository(IBitacoraRepository):
    def add_log(self, usuario_id: int | None, action: str, desc: str, modulo: str) -> None:
        with session_scope() as s:
            b = Bitacora(
                usuario_id=usuario_id,
                accion=action,
                descripcion=desc,
                modulo=modulo
            )
            s.add(b)
    
    def list_recent(self, limit: int = 50) -> list[Bitacora]:
        with session_scope() as s:
            return s.query(Bitacora).options(selectinload(Bitacora.usuario))\
                .order_by(Bitacora.fecha.desc()).limit(limit).all()

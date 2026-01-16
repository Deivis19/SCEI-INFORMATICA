from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Date, CheckConstraint, ForeignKey, Float, UniqueConstraint, LargeBinary
from datetime import date, datetime


class Base(DeclarativeBase):
    pass

class Direccion(Base):
    __tablename__ = "direccion"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    activo: Mapped[int] = mapped_column(Integer, default=1)

class Equipo(Base):
    __tablename__ = "equipo"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo_interno: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(300), nullable=False)
    marca: Mapped[str] = mapped_column(String(100), nullable=True)
    modelo: Mapped[str] = mapped_column(String(100), nullable=True)
    nro_serie: Mapped[str] = mapped_column(String(120), nullable=True)
    ubicacion: Mapped[str] = mapped_column(String(200), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="optimo")
    fecha_alta: Mapped[date] = mapped_column(Date, default=date.today)
    direccion_id: Mapped[int | None] = mapped_column(ForeignKey("direccion.id"), nullable=True)

    __table_args__ = (
        CheckConstraint("estado in ('optimo','defectuoso','inoperativo')", name="ck_equipo_estado"),
        UniqueConstraint("codigo_interno", "direccion_id", name="uq_equipo_codigo_dir"),
    )

    # Relaciones
    mantenimientos: Mapped[list["Mantenimiento"]] = relationship("Mantenimiento", back_populates="equipo")

class Mantenimiento(Base):
    __tablename__ = "mantenimiento"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    equipo_id: Mapped[int] = mapped_column(ForeignKey("equipo.id"), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, default=date.today)
    descripcion: Mapped[str] = mapped_column(String(500), nullable=False)
    estado_equipo: Mapped[str] = mapped_column(String(20), nullable=False, default="optimo")

    # Relaciones
    equipo: Mapped["Equipo"] = relationship("Equipo", back_populates="mantenimientos")

class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(150), nullable=True)
    rol: Mapped[str] = mapped_column(String(20), default="usuario") # admin, usuario
    email: Mapped[str] = mapped_column(String(100), nullable=True)
    # Security Questions (for non-admin users)
    respuesta_seguridad_1: Mapped[str] = mapped_column(String(20), nullable=True)  # DD/MM birthday
    respuesta_seguridad_2: Mapped[str] = mapped_column(String(100), nullable=True) # Parent name lowercase
    # Face recognition data (pickled numpy array or raw bytes)
    face_data = mapped_column(LargeBinary, nullable=True)

    bitacoras: Mapped[list["Bitacora"]] = relationship("Bitacora", back_populates="usuario")

class Bitacora(Base):
    __tablename__ = "bitacora"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    accion: Mapped[str] = mapped_column(String(50), nullable=False) # LOGIN, INSERT, UPDATE, DELETE
    descripcion: Mapped[str] = mapped_column(String(500), nullable=True)
    modulo: Mapped[str] = mapped_column(String(50), nullable=True) # Equipos, Direcciones...
    fecha: Mapped[datetime] = mapped_column(default=datetime.now)

    usuario: Mapped["User"] = relationship("User", back_populates="bitacoras")

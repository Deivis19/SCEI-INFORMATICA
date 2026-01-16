from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import os
import sys
import shutil
import sqlite3

def _resolve_db_path() -> Path:
    """Determina la ruta de la BD priorizando modo portable junto al ejecutable.
    Orden: (1) exe_dir/data/data.db, (2) AppData/SCEI/data.db, (3) paquete local.
    Copia DB semilla del bundle si existe y el destino no existe.
    """
    def _bundle_seed_db_path() -> Path | None:
        try:
            if not getattr(sys, "frozen", False):
                return None
            # 0) En modo onedir, los datas suelen quedar junto al ejecutable
            exe_dir = Path(sys.executable).parent
            candidate = exe_dir / "data.db"
            if candidate.exists():
                return candidate

            candidate = exe_dir / "data" / "data.db"
            if candidate.exists():
                return candidate

            candidate = exe_dir / "scei.db"
            if candidate.exists():
                return candidate

            # 1) En modo onefile, PyInstaller expone sys._MEIPASS
            base = Path(getattr(sys, "_MEIPASS", ""))
            if str(base):
                candidate = base / "data.db"
                if candidate.exists():
                    return candidate

                # Preferimos una BD semilla consistente con el proyecto (scei.db)
                candidate = base / "scei.db"
                if candidate.exists():
                    return candidate

                # Fallback por compatibilidad (si se empaqueta como data/data.db)
                candidate = base / "data" / "data.db"
                if candidate.exists():
                    return candidate
        except Exception:
            return None
        return None

    def _safe_count_equipos(db_path: Path) -> int | None:
        try:
            if not db_path.exists():
                return None
            con = sqlite3.connect(str(db_path))
            cur = con.cursor()
            cur.execute("SELECT COUNT(*) FROM equipo")
            n = int(cur.fetchone()[0])
            con.close()
            return n
        except Exception:
            try:
                con.close()
            except Exception:
                pass
            return None

    def _ensure_seeded(dest: Path) -> None:
        bundle_data = _bundle_seed_db_path()
        if not bundle_data or not bundle_data.exists():
            return

        if dest.exists():
            # Si el destino existe pero está vacío y el bundle tiene datos, reemplazar.
            try:
                dest_count = _safe_count_equipos(dest)
                seed_count = _safe_count_equipos(bundle_data)
                if seed_count is None or seed_count <= 0:
                    return

                # Si no podemos contar en el destino (por ejemplo tabla no existe/corrupta),
                # lo tratamos como vacío para permitir autocorrección.
                if dest_count is not None and dest_count > 0:
                    return

                backup = dest.with_suffix(dest.suffix + ".bak")
                try:
                    if not backup.exists():
                        shutil.copy2(dest, backup)
                except Exception:
                    pass
                try:
                    shutil.copy2(bundle_data, dest)
                except Exception:
                    pass
                return
            except Exception:
                return
        else:
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(bundle_data, dest)
            except Exception:
                pass

    # 1) AppData del usuario (prioritario para persistencia y compatibilidad)
    try:
        base_user = Path(os.environ.get("LOCALAPPDATA", Path.home()))
        user_dir = base_user / "SCEI"
        user_dir.mkdir(parents=True, exist_ok=True)
        db_path = user_dir / "data.db"
        if getattr(sys, "frozen", False):
            _ensure_seeded(db_path)
        # Probar escritura/lectura
        try:
            with open(db_path, 'ab'):
                pass
            return db_path
        except Exception:
            pass
    except Exception:
        pass

    # 2) Modo portable junto al ejecutable (fallback cuando AppData no es usable)
    try:
        if getattr(sys, "frozen", False):
            exe_dir = Path(sys.executable).parent
            portable_dir = exe_dir / "data"
            portable_dir.mkdir(parents=True, exist_ok=True)
            db_path = portable_dir / "data.db"
            _ensure_seeded(db_path)
            try:
                with open(db_path, 'ab'):
                    pass
                return db_path
            except Exception:
                pass
    except Exception:
        pass

    # 3) Desarrollo: carpeta local del paquete
    pkg_data = Path(__file__).resolve().parent / "data"
    pkg_data.mkdir(parents=True, exist_ok=True)
    return pkg_data / "data.db"

DB_PATH = _resolve_db_path()

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
    expire_on_commit=False,
)

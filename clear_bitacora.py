from sqlalchemy import create_engine, text
from scei.data.db import DB_PATH

try:
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM bitacora"))
        conn.commit()
    print("Bitacora cleared successfully.")
except Exception as e:
    print(f"Error clearing bitacora: {e}")

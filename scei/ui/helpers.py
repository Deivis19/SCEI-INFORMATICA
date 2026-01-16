
from ..data.repositories import list_direcciones

def direccion_nombre(direccion_id: int | None) -> str:
    if not direccion_id:
        return ""
    try:
        # Optimización: si list_direcciones es cacheado o rápido está bien, 
        # idealmente usaríamos get_direccion(id) pero list_direcciones está en memoria
        for d in list_direcciones():
            if d.id == direccion_id:
                return d.nombre or ""
    except Exception:
        pass
    return ""

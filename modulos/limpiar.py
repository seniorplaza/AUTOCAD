"""
limpiar.py — Eliminación de las entidades de ejemplo de la PLANTILLA.dxf.

Estrategia de dos pasos:
  1. Capas estructurales (PL-LIM-CASETA, CORREAS, etc.) → borrar SIEMPRE, en cualquier posición.
  2. Cualquier otra capa → borrar si la entidad está dentro de ZONA_X / ZONA_Y.
     (limpiar_modulo se llama ANTES de dibujar nada, así que todo lo que hay en la zona
      es basura del template de ejemplo.)
"""
from .config import ZONA_X, ZONA_Y

# Capas que se borran independientemente de su posición
_CAPAS_SIEMPRE = {
    'PL-LIM-CASETA', 'PL-PILARES', 'PL-PIL-DIB', 'CORREAS', 'CARRIL',
    'ALZ-EST-BA-DIB', 'ALZ-CER-DIB', 'Ejes', 'SOMBRAS', 'CUADROS',
    # PL-CER-DIB NO está aquí: las polilíneas de VARIACIONES (fuera de la zona)
    # deben sobrevivir para que seccion_ancho.py las pueda leer.
    # Las del módulo de ejemplo (dentro de ZONA_X/ZONA_Y) se borran por el filtro de zona.
}


def _punto_representativo(e):
    """Devuelve (x, y) representativo de la entidad, o None si no se puede obtener."""
    t = e.dxftype()
    try:
        if t == 'LINE':
            return e.dxf.start.x, e.dxf.start.y
        if t == 'LWPOLYLINE':
            pts = list(e.get_points())
            return (pts[0][0], pts[0][1]) if pts else None
        if t in ('MTEXT', 'TEXT', 'INSERT'):
            return e.dxf.insert.x, e.dxf.insert.y
        if t == 'DIMENSION':
            return e.dxf.defpoint.x, e.dxf.defpoint.y
        if t in ('CIRCLE', 'ARC'):
            return e.dxf.center.x, e.dxf.center.y
        if t == 'POINT':
            return e.dxf.location.x, e.dxf.location.y
        if t == 'HATCH':
            for path in e.paths.paths:
                if hasattr(path, 'vertices') and path.vertices:
                    return path.vertices[0][0], path.vertices[0][1]
                if hasattr(path, 'edges') and path.edges:
                    edge = path.edges[0]
                    if hasattr(edge, 'start'):  return edge.start[0],  edge.start[1]
                    if hasattr(edge, 'center'): return edge.center[0], edge.center[1]
        if t == 'SPLINE':
            cp = list(e.control_points)
            return (cp[0][0], cp[0][1]) if cp else None
        if t in ('ELLIPSE', 'SOLID', 'TRACE'):
            return e.dxf.center.x, e.dxf.center.y
        if t == 'ARCALIGNEDTEXT':
            try: return e.dxf.insert.x, e.dxf.insert.y
            except Exception: pass
            try: return e.dxf.center.x, e.dxf.center.y
            except Exception: pass
    except Exception:
        pass
    return None


def _en_zona(e):
    try:
        layer = e.dxf.layer
    except Exception:
        # Entidades sin layer estándar (ARCALIGNEDTEXT, etc.):
        # borrar si tienen punto representativo dentro de la zona
        pt = _punto_representativo(e)
        if pt:
            x, y = pt
            return ZONA_X[0] < x < ZONA_X[1] and ZONA_Y[0] < y < ZONA_Y[1]
        return False

    # Paso 1: capas estructurales → borrar siempre
    if layer in _CAPAS_SIEMPRE:
        return True

    # Paso 2: cualquier otra capa → borrar si está en la zona del template
    pt = _punto_representativo(e)
    if pt:
        x, y = pt
        return ZONA_X[0] < x < ZONA_X[1] and ZONA_Y[0] < y < ZONA_Y[1]
    return False


def limpiar_modulo(msp):
    borrar = [e for e in msp if _en_zona(e)]
    for e in borrar:
        msp.delete_entity(e)
    print(f"  Limpiadas {len(borrar)} entidades")

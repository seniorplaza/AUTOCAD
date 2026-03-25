"""
bloques.py — Inserción de bloques de recuadros de la plantilla con atributos dinámicos.
RECUADRO H PERFIL BASE, PILARES-MUÑONES, TÍTULO PLANO, Nº UD, CARRIL, TABLERO Y SUELO, SERIE.
"""
from ezdxf.enums import TextEntityAlignment
from .dxf_utils import _attribs
from .plano_base import _munon_pilar_str


def dibujar_bloques_recuadros(msp, doc, x0, y0, x1, y1, hbase, long_pilar, A,
                               panel_grosor, g_carril, panel_tipo, serie,
                               suministro, tipo_tablero, acabado):
    cx = (x0 + x1) / 2.0

    str_mun, str_pil = _munon_pilar_str(A, long_pilar, panel_grosor)
    mun_val = str_mun.replace('MUÑONES ', '').strip()
    pil_val = str_pil.replace('PILARES ', '').strip()

    tablero_val = tipo_tablero.upper()
    acabado_str = (acabado or '').strip()
    tablero_suelo_val = f"{tablero_val} + {acabado_str}" if acabado_str else tablero_val

    # Número de unidades desde campo serie
    try:
        partes = (serie or '').replace(' ','').split('-')
        if len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit():
            n_uds = int(partes[1]) - int(partes[0]) + 1
        elif len(partes) >= 3:
            n_uds = len(partes)
        else:
            n_uds = 1
    except Exception:
        n_uds = 1
    uds_val = f"{n_uds} UNIDADES" if n_uds != 1 else "1 UNIDAD"

    # 1. RECUADRO H PERFIL BASE Xmm
    ref = msp.add_blockref('RECUADRO H PERFIL BASE Xmm',
                           insert=(x1, y1+909.5), dxfattribs={'layer': 'Cotas'})
    _attribs(ref, {'HBASE': str(hbase)}, doc)

    # 2. RECUADROS MEDIDAS PILARES - MUÑONES
    ref = msp.add_blockref('RECUADROS MEDIDAS PILARES - MUÑONES',
                           insert=(cx, y1+1784.3), dxfattribs={'layer': 'TEXTO'})
    _attribs(ref, {'MUÑONES': mun_val, 'PILARES': pil_val}, doc)

    # 3. RECUADRO TÍTULO PLANO
    ref = msp.add_blockref('RECUADRO TÍTULO PLANO',
                           insert=(cx, y1+3009.6), dxfattribs={'layer': 'Cotas'})
    _attribs(ref, {'TABLERO': tablero_val}, doc)

    # Textos *COMPROBAR centrados en el módulo
    for dy, txt in [
        (2349.0, '*COMPROBAR LA MEDIDA DEL TABLERO ANTES DE SOLDAR'),
        (2093.0, '*COMPROBAR LAS DIMENSIONES DE LOS MUÑONES CON LOS PILARES'),
    ]:
        t_ent = msp.add_text(txt, dxfattribs={'layer': 'TEXTO', 'height': 82.9})
        t_ent.set_placement((cx, y1+dy), align=TextEntityAlignment.CENTER)

    # 4-5. Bloques laterales (se omiten para módulo mini A<=1190)
    if A > 1190:
        ud_x = max(x1+714.2, cx + 1900.0)
        ref = msp.add_blockref('RECUADRO NÚMERO DE UD (MÓDULOS) NUMERO SERIE',
                               insert=(ud_x, y1+2952.2595), dxfattribs={'layer': 'Cotas'})
        _attribs(ref, {'4UNIDADES_1UNIDAD': uds_val}, doc)

        ref = msp.add_blockref('CARRIL PARA PANEL DE Xmm',
                               insert=(x1+479.9077, y1+372.5578), dxfattribs={'layer': 'Cotas'})
        _attribs(ref, {'CARRIL': str(g_carril)}, doc)
        # Arco líder (amarillo discontinuo) desde el bloque hacia el carril
        _arc = msp.add_arc(center=(x1+3202.4, y1-2906.7), radius=4262.1,
                           start_angle=129.7, end_angle=140.1,
                           dxfattribs={'layer': 'Cotas', 'color': 2, 'linetype': 'TRAZOS2', 'ltscale': 10})
        _arc.transparency = 0.5

    cy = (y0 + y1) / 2.0

    # 7. RECUADRO TABLERO Y SUELO
    ref = msp.add_blockref('RECUADRO TABLERO Y SUELO',
                           insert=(cx, cy - 198.3), dxfattribs={'layer': 'TEXTO'})
    _attribs(ref, {'TABLERO_SUELO': tablero_suelo_val}, doc)

    # 8. BLOQUE NÚMERO SERIE
    ref = msp.add_blockref('BLOQUE NÚMERO SERIE',
                           insert=(cx, cy + 225.6), dxfattribs={'layer': 'TEXTO'})
    _attribs(ref, {'SERIE': serie or '-'}, doc)

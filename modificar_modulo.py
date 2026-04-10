"""
modificar_modulo.py  v8
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTEXTO GENERAL DEL PROYECTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Script Python para generación automática de planos DXF de módulos prefabricados.
Lee un CSV exportado desde el gestor de pedidos (gestor.html) y una PLANTILLA.dxf,
y genera un DXF por pedido con TODOS los planos apilados verticalmente en el
modelspace (uno debajo de otro, con separación entre ellos).

ESTRUCTURA DE MÓDULOS:
  modificar_modulo.py     ← punto de entrada (este archivo): CSV, menú, main
  modulos/
    config.py             ← constantes: rutas, COL, MAPA_RAL, offsets carriles, zonas
    calculos.py           ← calc_hbase, calc_hcubierta, calc_correas, grosor_carril...
    dxf_utils.py          ← cota_h, cota_v, _attribs, _rect_redondeado, hatch
    limpiar.py            ← limpiar_modulo (borra entidades de ejemplo de la plantilla)
    plano_base.py         ← insertar_pilares, dibujar_carriles, dibujar_alzado_base,
                             dibujar_zona_derecha, dibujar_textos_modulo
    seccion_ancho.py      ← _perfil_seccion, dibujar_seccion_ancho (VARIACIONES)
    bloques.py            ← dibujar_bloques_recuadros (todos los bloques con attribs)
    generar.py            ← generar_modulo (orquesta todo el proceso por fila)

EJECUCIÓN:
  python modificar_modulo.py              → abre selector de archivo (tkinter)
  python modificar_modulo.py pedidos.csv → usa el CSV directamente
  python modificar_modulo.py pedidos.csv --todos → genera todos sin menú

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PLANOS A GENERAR (apilados en modelspace, misma PLANTILLA.dxf para todos)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. ESTRUCTURA BASE (implementado - v8)
   ── Planta del módulo ──────────────────────────────────────────────────────
   - Contorno módulo (capa PL-LIM-CASETA)
   - Pilares en esquinas (capa PL-PILARES) - bloque según ancho y grosor panel
   - Correas (capa CORREAS, cian) - posición según tipo tablero (Fenólico/Hidrófugo)
   - Carriles (capa CARRIL, gris) - grosor según panel, longitud según ancho módulo
   - Cotas nativas DXF (dimstyle PMP-T-50 entre correas, PMP-T-60 totales)
   - Cajetín con atributos: OB, RAL, N/S, SUMINISTRO, FECHA, OFERTA

   ── Alzado de la base (encima del módulo) ─────────────────────────────────
   - Rectángulo verde (capa ALZ-EST-BA-DIB): ancho = L módulo, alto = hbase mm
   - Bloques CORREA BASE: uno por correa centrado en su eje
   - Cota vertical PMP-T-75 del hbase a la izquierda
   - Bloques de recuadros con atributos dinámicos (pilares, muñones, título, serie, etc.)

   ── Sección lado ancho (a la derecha, plano estructura base) ──────────────
   - Perfiles del larguero base (PL-CER-DIB) desde VARIACIONES SECCIÓN_LARGUERO_BASE
   - Tablero (color 2 amarillo): 18mm fenólico / 19mm hidrófugo
   - Correa (color 4 cian): siempre 99mm de alto
   - BLOQUE TABLERO SECCIÓN con atributos: TIPO_TABLERO, TABLERO, NÚMERO_GROSOR_TABLERO

2. ESTRUCTURA CUBIERTA (pendiente)
3. DISTRIBUCIÓN DE PANELES (pendiente)
4. PLANO DE REVISIÓN (pendiente)
5. PLANO DE ELECTRICIDAD (pendiente)
6. PLANO DE SANEAMIENTO Y FONTANERÍA (pendiente)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESTRUCTURA DEL CSV (separador ";", encoding utf-8-sig)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Col 0  fecha           | Col 1  oferta          | Col 2  numPedido
Col 3  cliente         | Col 4  destino         | Col 5  serie
Col 6  l (largo mm)    | Col 7  a (ancho mm)    | Col 8  h (alto mm)
Col 9  estBase         | Col 10 estCubierta     | Col 11 estPilar
Col 12 cubierta (PANEL/ESTÁNDAR)              | Col 13 panelGrosor     | Col 14 panelTipo
Col 15 base (tipo tablero)                    | Col 16 acabado         | Col 17 suministro
Col 18 perfilado       | Col 19 colorPanel      | Col 20 colorEstructura
Col 21 colorCarpinteria | Col 22 extra (notas)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REGLAS IMPORTANTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LONGITUD DEL PILAR:
  - Los campos L, A, H del CSV son LARGO, ANCHO y ALTURA INTERIOR del módulo.
  - El pilar siempre mide H_interior + 25mm.

ALTURA PERFIL BASE (hbase):
  - "BASE AISLADA e40 / CARRIL > e50" significa panel > 50mm (no >= 50).
  - Panel exactamente 50mm usa carril e50 → hbase NO sube a 160mm.

ÚLTIMA CORREA:
  - Siempre al punto medio de la última cota de tablero.

GROSORES DE PANEL → CARRIL Y PILAR:
  panel <= 40mm → carril 40mm, pilar estándar (PL - pilar)
  panel <= 50mm → carril 50mm, PILAR PANEL 50
  panel <= 70mm → carril 60mm, PILAR PANEL 60
  panel <= 90mm → carril 80mm, PILAR PANEL 80
  panel >  90mm → carril 100mm, PILAR PANEL 100
"""
import sys
import os
import csv
from collections import OrderedDict, Counter

# Forzar UTF-8 en stdout para evitar errores en consolas Windows con cp1252
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import ezdxf  # noqa: F401
except ImportError:
    os.system("pip install ezdxf --break-system-packages -q")
    import ezdxf  # noqa: F401

import json as _json

from modulos.config   import PLANTILLA_DXF, CARPETA_SALIDA, COL
from modulos.generar  import generar_modulo
from modulos.adosado  import generar_adosado


# ─── LECTURA CSV ──────────────────────────────────────────────────────────────

def leer_csv(ruta):
    filas = []
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        for i, fila in enumerate(csv.reader(f, delimiter=";")):
            if i == 0: continue
            if any(campo.strip() for campo in fila):
                filas.append(fila)
    return filas


def _c(fila, col):
    idx = COL.get(col, -1)
    return fila[idx].strip() if 0 <= idx < len(fila) else ""


def _clave_pedido(fila):
    return _c(fila, 'numPedido')


# ─── MENÚ INTERACTIVO ─────────────────────────────────────────────────────────

def mostrar_menu(grupos):
    print("\n─── PEDIDOS ───")
    for i, (clave, filas_g) in enumerate(grupos, 1):
        f0 = filas_g[0]
        cliente = _c(f0, 'cliente')
        if len(filas_g) == 1:
            f = filas_g[0]
            print(f"  [{i:>2}]  {clave:15}  {cliente:15}  {_c(f,'destino'):15}  "
                  f"L={_c(f,'l')} A={_c(f,'a')}  {_c(f,'base') or 'HIDRÓFUGO':12}  {_c(f,'panelGrosor') or '-'}mm")
        else:
            print(f"  [{i:>2}]  {clave:15}  {cliente:15}  ({len(filas_g)} planos)")
            for j, f in enumerate(filas_g, 1):
                mod  = _c(f, 'modulo') or f'M{j}'
                tipo = 'CONJ' if _c(f,'conjunto').strip().lower() == 'true' else 'AIS '
                print(f"         {mod}  {tipo}  L={_c(f,'l')} A={_c(f,'a')}  {_c(f,'destino'):15}  "
                      f"{_c(f,'base') or 'HIDRÓFUGO':12}  {_c(f,'panelGrosor') or '-'}mm  {_c(f,'extra')}")
    print("─────────────────")
    while True:
        try:
            entrada = input("Número de pedido (0=todos, 1,2,3=varios): ").strip()
        except EOFError:
            continue
        if not entrada:
            continue
        try:
            nums = [int(x.strip()) for x in entrada.split(",")]
        except ValueError:
            continue
        if 0 in nums:
            return [f for _, filas_g in grupos for f in filas_g]
        if all(1 <= n <= len(grupos) for n in nums):
            result = []
            for n in nums:
                result.extend(grupos[n-1][1])
            return result


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    modo_todos = "--todos" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if args:
        ruta_csv = args[0]
    else:
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk(); root.withdraw()
            ruta_csv = filedialog.askopenfilename(
                title="Selecciona el CSV del Gestor",
                filetypes=[("CSV","*.csv"),("Todos","*.*")])
            root.destroy()
        except:
            ruta_csv = input("Ruta CSV: ").strip().strip('"')

    if not ruta_csv or not os.path.isfile(ruta_csv):
        print("CSV no encontrado."); input(); sys.exit(1)
    if not os.path.isfile(PLANTILLA_DXF):
        print(f"No encuentro: {PLANTILLA_DXF}"); input(); sys.exit(1)

    filas = leer_csv(ruta_csv)
    if not filas:
        print("CSV vacío."); input(); sys.exit(1)

    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    grupos_dict = OrderedDict()
    for fila in filas:
        grupos_dict.setdefault(_clave_pedido(fila), []).append(fila)
    grupos = list(grupos_dict.items())

    if modo_todos:
        pedidos = filas
    elif len(filas) == 1:
        pedidos = filas
    else:
        pedidos = mostrar_menu(grupos)

    # Agrupar por numPedido manteniendo orden
    grupos_np = OrderedDict()
    for fila in pedidos:
        grupos_np.setdefault(_c(fila,'numPedido'), []).append(fila)

    for np, filas_np in grupos_np.items():
        destino0    = _c(filas_np[0], 'destino')
        base_nombre = f"{np}-{destino0}".replace("/","-").replace(" ","_")

        # ── Nombres únicos por fila ───────────────────────────────────────────
        # Si varios módulos del mismo pedido tienen el mismo modulo (ej. todos M1)
        # se añade sufijo -1, -2, -3... para evitar que los DXF se sobreescriban.
        _mods = [_c(f, 'modulo') or f'M{k+1}' for k, f in enumerate(filas_np)]
        _frec = Counter(_mods)
        _visto = {}
        _nombre_unico = {}
        for k, fila in enumerate(filas_np):
            m = _mods[k]
            if _frec[m] > 1:
                _visto[m] = _visto.get(m, 0) + 1
                _nombre_unico[id(fila)] = f"{base_nombre}-{m}-{_visto[m]}"
            else:
                _nombre_unico[id(fila)] = f"{base_nombre}-{m}"

        def _nombre(fila):
            return _nombre_unico[id(fila)]

        # ── Clasificar filas ──────────────────────────────────────────────────
        # conjuntoVinculado='' (CSV antiguo) → vinculado por compatibilidad
        # conjuntoVinculado='true'  → comparte adosamiento con el resto del grupo
        # conjuntoVinculado='false' → independiente, tiene su propio adosamiento
        def _vinculado(f):
            return _c(f, 'conjuntoVinculado').strip().lower() != 'false'

        filas_conj_vinc = [f for f in filas_np
                           if _c(f,'conjunto').strip().lower() == 'true' and _vinculado(f)]
        filas_conj_solo = [f for f in filas_np
                           if _c(f,'conjunto').strip().lower() == 'true' and not _vinculado(f)]
        filas_ais       = [f for f in filas_np
                           if _c(f,'conjunto').strip().lower() != 'true']

        # ── CONJUNTO VINCULADO (un solo DXF adosado compartido) ───────────────
        adosamiento = None
        for f in filas_conj_vinc:
            raw = _c(f, 'adosamiento').strip()
            if raw:
                try:
                    adosamiento = _json.loads(raw)
                    break
                except Exception:
                    pass

        if filas_conj_vinc and adosamiento and adosamiento.get('placed'):
            nombre   = f"{base_nombre}-ADO"
            ruta_sal = os.path.join(CARPETA_SALIDA, f"{nombre}.dxf")
            print(f"\nGenerando (adosado): {nombre}")
            generar_adosado(filas_conj_vinc, adosamiento, PLANTILLA_DXF, ruta_sal)

        elif filas_conj_vinc:
            # vinculado sin layout → fallback individual
            for fila in filas_conj_vinc:
                nombre   = _nombre(fila)
                ruta_sal = os.path.join(CARPETA_SALIDA, f"{nombre}.dxf")
                print(f"\nGenerando: {nombre}")
                generar_modulo(fila, PLANTILLA_DXF, ruta_sal)

        # ── CONJUNTO INDEPENDIENTE (un DXF por fila, con su propio adosamiento) ─
        for fila in filas_conj_solo:
            nombre   = _nombre(fila)
            ruta_sal = os.path.join(CARPETA_SALIDA, f"{nombre}.dxf")
            raw_ado  = _c(fila, 'adosamiento').strip()
            ado_solo = None
            if raw_ado:
                try:
                    ado_solo = _json.loads(raw_ado)
                except Exception:
                    pass
            if ado_solo and ado_solo.get('placed'):
                print(f"\nGenerando (conj. independiente): {nombre}")
                generar_adosado([fila], ado_solo, PLANTILLA_DXF, ruta_sal)
            else:
                print(f"\nGenerando: {nombre}")
                generar_modulo(fila, PLANTILLA_DXF, ruta_sal)

        # ── MÓDULOS AISLADOS ──────────────────────────────────────────────────
        for fila in filas_ais:
            if len(filas_np) == 1:
                nombre = base_nombre          # único módulo del pedido: nombre limpio
            else:
                nombre = _nombre(fila)
            ruta_sal = os.path.join(CARPETA_SALIDA, f"{nombre}.dxf")
            print(f"\nGenerando: {nombre}")
            generar_modulo(fila, PLANTILLA_DXF, ruta_sal)

    print(f"\n{chr(9472)*50}\nArchivos en: {CARPETA_SALIDA}\n{chr(9472)*50}")
    input("\nPulsa Enter para salir...")


if __name__ == "__main__":
    try:
        main()
    except Exception as _e:
        print(f"\nERROR: {_e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPulsa Enter para salir...")

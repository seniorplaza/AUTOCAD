# Arquitectura — modificar_modulo

```mermaid
flowchart TB
    classDef entry    fill:#1a1a2e,stroke:#e94560,stroke-width:2px,color:#fff
    classDef io       fill:#16213e,stroke:#0f3460,stroke-width:2px,color:#a8d8ea
    classDef core     fill:#0f3460,stroke:#533483,stroke-width:2px,color:#fff
    classDef draw     fill:#533483,stroke:#e94560,stroke-width:1.5px,color:#fff
    classDef util     fill:#1a1a2e,stroke:#533483,stroke-width:1.5px,color:#c9b8e8
    classDef output   fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#a7f3d0

    CSV(["📄 pedidos.csv"]):::io
    PLANTILLA(["📐 PLANTILLA.dxf"]):::io
    OUT(["📁 Generados/*.dxf"]):::output

    MAIN["🚀 modificar_modulo.py\n─────────────────\nleer_csv\nmostrar_menu\nmain"]:::entry

    subgraph modulos["  📦 modulos/  "]
        direction TB

        CONFIG["⚙️ config.py\n─────────────────\nRutas · COL\nMAPA_RAL\nCARRIL_OFS_*\nZONA_X / ZONA_Y"]:::util

        CALC["🧮 calculos.py\n─────────────────\ncalc_hbase\ncalc_hcubierta\ncalc_correas\ngrosor_carril\nnombre_bloque_pilar\nhex_a_ral"]:::core

        UTILS["🔧 dxf_utils.py\n─────────────────\ncota_h · cota_v\n_attribs\n_rect_redondeado\n_hatch_rect_redondeado"]:::core

        LIMPIAR["🧹 limpiar.py\n─────────────────\nlimpiar_modulo\n(borra template\nen zona+capas)"]:::util

        BASE["🏗️ plano_base.py\n─────────────────\ninsertar_pilares\ndibujar_carriles\ndibujar_alzado_base\ndibujar_zona_derecha\ndibujar_textos_modulo"]:::draw

        SECCION["📐 seccion_ancho.py\n─────────────────\n_perfil_seccion\ndibujar_seccion_ancho\n(VARIACIONES block)"]:::draw

        BLOQUES["🧩 bloques.py\n─────────────────\ndibujar_bloques_recuadros\n(INSERTs + ATTRIBs)"]:::draw

        GENERAR["⚡ generar.py\n─────────────────\ngenerar_modulo\n(orquesta todo)"]:::entry
    end

    CSV      --> MAIN
    MAIN     --> GENERAR
    PLANTILLA--> GENERAR

    CONFIG  --> CALC
    CONFIG  --> UTILS
    CONFIG  --> LIMPIAR
    CONFIG  --> GENERAR

    CALC    --> GENERAR
    UTILS   --> BASE
    UTILS   --> SECCION
    UTILS   --> BLOQUES
    LIMPIAR --> GENERAR
    BASE    --> GENERAR
    SECCION --> GENERAR
    BLOQUES --> GENERAR

    GENERAR --> OUT
```

---

## Orden de ejecución dentro de `generar_modulo`

```mermaid
flowchart LR
    classDef step fill:#0f3460,stroke:#533483,color:#fff,stroke-width:1.5px
    classDef save fill:#064e3b,stroke:#10b981,color:#a7f3d0,stroke-width:2px

    A("1️⃣ calc_*\ndimensiones"):::step
    B("2️⃣ limpiar_modulo\nborra template"):::step
    C("3️⃣ Marco A3\ncajetín escalado"):::step
    D("4️⃣ Contorno\nCorreas · Carriles"):::step
    E("5️⃣ Cotas\nh · v · tablero"):::step
    F("6️⃣ alzado_base\nrect verde +\nCORREA BASE"):::step
    G("7️⃣ seccion_ancho\nperfiles +\ntablero + correa"):::step
    H("8️⃣ bloques_recuadros\nINSERTs ATTRIBs"):::step
    I("9️⃣ insertar_pilares\n⬆️ draw order TOP"):::step
    J("💾 saveas\n*.dxf"):::save

    A-->B-->C-->D-->E-->F-->G-->H-->I-->J
```

---

## Qué módulo tocar según el síntoma

| Síntoma / cambio | Módulo |
|---|---|
| Cambiar rutas, offsets de carriles, zona de limpieza | `config.py` |
| Cálculo de hbase, correas, pilares, grosor carril | `calculos.py` |
| Cotas mal generadas, attribs de bloque incorrectos | `dxf_utils.py` |
| Quedan restos del template en el DXF generado | `limpiar.py` |
| Pilares, carriles, alzado verde, textos del módulo | `plano_base.py` |
| Sección del lado ancho (tablero, correa, perfiles) | `seccion_ancho.py` |
| Bloques recuadros (pilares, muñones, título, serie…) | `bloques.py` |
| Flujo general, marco A3, cajetín, orden de llamadas | `generar.py` |
| CSV, menú interactivo, arranque del script | `modificar_modulo.py` |

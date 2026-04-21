// ═══ ADOSAMIENTO UNDO/REDO ═══════════════════════════════════════════════════
        let adoUndoStack = [];
        let adoRedoStack = [];

        function adoPushUndo() {
            adoUndoStack.push({
                placed:  JSON.parse(JSON.stringify(adoState.placed)),
                faceMap: JSON.parse(JSON.stringify(adoState.faceMap)),
            });
            if (adoUndoStack.length > 50) adoUndoStack.shift();
            adoRedoStack = [];
        }

        function adoUndo() {
            if (!adoUndoStack.length) return;
            adoRedoStack.push({
                placed:  JSON.parse(JSON.stringify(adoState.placed)),
                faceMap: JSON.parse(JSON.stringify(adoState.faceMap)),
            });
            const snap = adoUndoStack.pop();
            adoState.placed  = snap.placed;
            adoState.faceMap = snap.faceMap;
            adoPickerClose(); adoWallMenuClose();
            adoRender();
        }

        function adoRedo() {
            if (!adoRedoStack.length) return;
            adoUndoStack.push({
                placed:  JSON.parse(JSON.stringify(adoState.placed)),
                faceMap: JSON.parse(JSON.stringify(adoState.faceMap)),
            });
            const snap = adoRedoStack.pop();
            adoState.placed  = snap.placed;
            adoState.faceMap = snap.faceMap;
            adoPickerClose(); adoWallMenuClose();
            adoRender();
        }

// ═══ ADOSAMIENTO STATE ═══════════════════════════════════════════════════════
        let adoState = {
            groupKey:     null,
            rowId:        null,  // id de la fila CONJ que se está editando
            grupoRowIds:  [],    // ids de todas las filas del grupo (si hay conjuntoGrupo)
            pool:         [],    // [{poolId, rowId, modulo, l, a, ...}]
            placed:       [],    // [{key, poolId, modulo, l, a, x, y}]
            pending:      null,  // {targetKey, dir} — esperando selección de módulo
            faceMap:      {},    // {key: {face: 'cerrado'|'abierto'}}
            pendingWall:  null,  // wall pair activo en el menú
            pendingExtFace: null, // {key, face, svgCx, svgCy} — cara exterior activa
            dragging:     null,  // {key, offX, offY, origX, origY} — drag en curso
            renderParams: null,  // {scale, dx, dy, W, H} — última renderización
            zoom:         1,     // factor de zoom del canvas
        };

// ═══ ADOSAMIENTO FUNCTIONS ═══════════════════════════════════════════════════
        function openAdosamientoConfig(itemId) {
            const row = orders.find(o => o.id === itemId);
            if (!row || !row.conjunto) return;

            adoState.rowId    = itemId;
            adoState.groupKey = (row.oferta||'') + '||' + (row.numPedido||'') + '||' + (row.cliente||'');

            // Determinar filas del grupo: si está vinculado, incluir todas las filas
            // CONJ vinculadas del mismo pedido; si no, solo esta fila
            let grupoRows;
            if (row.conjuntoVinculado) {
                grupoRows = orders.filter(o =>
                    (o.oferta||'') === (row.oferta||'') &&
                    (o.numPedido||'') === (row.numPedido||'') &&
                    (o.cliente||'') === (row.cliente||'') &&
                    o.conjunto &&
                    o.conjuntoVinculado
                );
            } else {
                grupoRows = [row];
            }
            adoState.grupoRowIds = grupoRows.map(r => r.id);

            // Construir pool con los módulos de todas las filas del grupo
            adoState.pool = [];
            grupoRows.forEach(r => {
                const qty = Math.max(1, parseInt(r.cantidad) || 1);
                for (let i = 0; i < qty; i++) {
                    adoState.pool.push({
                        poolId:      `${r.id}_${i}`,
                        rowId:       r.id,
                        modulo:      r.modulo || 'M1',
                        l:           parseInt(r.l) || 6000,
                        a:           parseInt(r.a) || 2350,
                        panelGrosor: r.panelGrosor || '',
                        base:        r.base || 'HIDRÓFUGO',
                        acabado:     r.acabado || '',
                    });
                }
            });

            // Cargar layout: buscar la primera fila del grupo que tenga config guardada
            const configRow = grupoRows.find(r => r.adosamiento && r.adosamiento.placed && r.adosamiento.placed.length) || grupoRows[0];
            if (configRow.adosamiento && configRow.adosamiento.placed && configRow.adosamiento.placed.length) {
                const validPoolIds = new Set(adoState.pool.map(p => p.poolId));
                const usedPoolIds  = new Set();
                adoState.placed = JSON.parse(JSON.stringify(configRow.adosamiento.placed))
                    .filter(p => {
                        if (!validPoolIds.has(p.poolId)) return false;
                        if (usedPoolIds.has(p.poolId)) return false;
                        usedPoolIds.add(p.poolId);
                        return true;
                    });
                if (!adoState.placed.length) {
                    const p = adoState.pool[0];
                    adoState.placed = [{ key:'k0', poolId:p.poolId, modulo:p.modulo, l:p.l, a:p.a, x:0, y:0 }];
                }
            } else {
                const p = adoState.pool[0];
                adoState.placed = [{ key:'k0', poolId:p.poolId, modulo:p.modulo, l:p.l, a:p.a, x:0, y:0 }];
            }

            // Cargar faceMap guardado
            adoState.faceMap = (configRow.adosamiento && configRow.adosamiento.faceMap)
                               ? JSON.parse(JSON.stringify(configRow.adosamiento.faceMap))
                               : {};

            adoState.pending = null;
            adoState.pendingWall = null;
            adoState.zoom = 1;
            adoUndoStack = [];
            adoRedoStack = [];
            document.body.style.overflow = 'hidden';
            document.getElementById('adoModal').style.display = 'flex';
            setTimeout(adoRender, 30); // esperar a que el DOM esté pintado
        }

        function adoClose() {
            document.body.style.overflow = '';
            document.getElementById('adoModal').style.display = 'none';
            adoPickerClose();
            adoWallMenuClose();
            const dimEd = document.getElementById('adoDimEditor');
            if (dimEd) dimEd.remove();
        }

        function adoModalBackdrop(e) {
            if (e.target === document.getElementById('adoModal')) adoClose();
        }

        function adoReset() {
            adoPushUndo();
            const p = adoState.pool[0];
            adoState.placed = [{ key:'k0', poolId:p.poolId, modulo:p.modulo, l:p.l, a:p.a, x:0, y:0 }];
            adoState.faceMap = {};
            adoState.zoom = 1;
            adoPickerClose();
            adoWallMenuClose();
            adoRender();
        }

        function adoUnplaced() {
            const used = new Set(adoState.placed.map(p => p.poolId));
            return adoState.pool.filter(p => !used.has(p.poolId));
        }

        function adoRender() {
            const wrap = document.getElementById('adoCanvasWrap');
            const svg  = document.getElementById('adoSvg');
            const W = wrap.clientWidth  || 800;
            const H = wrap.clientHeight || 400;
            svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
            svg.setAttribute('width',  W);
            svg.setAttribute('height', H);
            // Limpiar todo excepto el picker
            while (svg.firstChild) svg.removeChild(svg.firstChild);
            const _dimEd = document.getElementById('adoDimEditor');
            if (_dimEd) _dimEd.remove();

            if (!adoState.placed.length) return;

            // BBox en mm
            let x0mm = Infinity, y0mm = Infinity, x1mm = -Infinity, y1mm = -Infinity;
            adoState.placed.forEach(m => {
                x0mm = Math.min(x0mm, m.x);        y0mm = Math.min(y0mm, m.y);
                x1mm = Math.max(x1mm, m.x + m.l);  y1mm = Math.max(y1mm, m.y + m.a);
            });

            const PAD = 70;
            const scale = Math.min(
                (W - PAD*2) / Math.max(x1mm - x0mm, 1),
                (H - PAD*2) / Math.max(y1mm - y0mm, 1),
                0.28
            ) * (adoState.zoom || 1);
            const dx = PAD + ((W - PAD*2) - (x1mm - x0mm)*scale) / 2 - x0mm*scale;
            const dy = PAD + ((H - PAD*2) - (y1mm - y0mm)*scale) / 2 - y0mm*scale;

            // En SVG Y crece hacia abajo → invertimos respecto al eje mm
            const svgX = mmX => dx + mmX * scale;
            const svgY = mmY => H - (dy + mmY * scale);

            // Guardar params para conversión durante drag y cotas
            adoState.renderParams = { scale, dx, dy, W, H, x0mm, y0mm };

            // Configurar eventos de drag y zoom en el SVG (una sola vez)
            if (!svg._adoDragSetup) {
                svg._adoDragSetup = true;
                svg.addEventListener('mousemove', e => adoDragMove(e));
                svg.addEventListener('mouseup',    () => adoDragEnd());
                svg.addEventListener('mouseleave', () => { if (adoState.dragging) adoDragEnd(); });
                svg.addEventListener('wheel', e => {
                    e.preventDefault();
                    const delta = e.deltaY < 0 ? 1.1 : 0.9;
                    adoState.zoom = Math.min(Math.max((adoState.zoom || 1) * delta, 0.3), 5);
                    adoRender();
                }, { passive: false });
            }

            const unplaced = adoUnplaced();
            const canAdd = unplaced.length > 0;
            const PR = 15; // radio botón (+)

            // ── Guías inteligentes de alineación (durante drag) ───────────────
            if (adoState.dragging) {
                const { guideX, guideY } = adoState.dragging;
                const addGuide = (x1, y1, x2, y2) => {
                    const gl = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                    Object.entries({ x1, y1, x2, y2,
                        stroke: '#f59e0b', 'stroke-width': 1.5,
                        'stroke-dasharray': '6,3', opacity: 0.85 })
                        .forEach(([k, v]) => gl.setAttribute(k, v));
                    svg.appendChild(gl);
                };
                if (guideX !== null) addGuide(svgX(guideX), 0, svgX(guideX), H);
                if (guideY !== null) addGuide(0, svgY(guideY), W, svgY(guideY));
            }

            adoState.placed.forEach(m => {
                const sx = svgX(m.x),       sy = svgY(m.y + m.a);
                const sw = m.l * scale,     sh = m.a * scale;
                const col = ADO_COLORS[m.modulo] || ADO_COLORS['M1'];
                // Datos extra desde el pool
                const slot = adoState.pool.find(p => p.poolId === m.poolId) || {};

                const isDragging   = adoState.dragging && adoState.dragging.key === m.key;
                const isSwapTarget = adoState.dragging && adoState.dragging.swapTarget === m.key;

                const g = document.createElementNS('http://www.w3.org/2000/svg','g');
                g.style.cursor = isDragging ? 'grabbing' : 'grab';

                // Rectángulo
                const rect = document.createElementNS('http://www.w3.org/2000/svg','rect');
                Object.entries({ x:sx, y:sy, width:sw, height:sh,
                    fill:   isSwapTarget ? 'rgba(20,184,166,0.25)' : col.fill,
                    stroke: isSwapTarget ? '#5eead4' : (isDragging ? 'rgba(255,255,255,0.6)' : col.stroke),
                    'stroke-width': (isDragging || isSwapTarget) ? 2.5 : 1.5, rx:4 })
                    .forEach(([k,v]) => rect.setAttribute(k,v));
                if (isDragging) rect.setAttribute('opacity', '0.65');
                g.appendChild(rect);

                // Iniciar drag al pulsar sobre el módulo
                g.addEventListener('mousedown', e => {
                    if (e.button !== 0) return;
                    // No iniciar si se pulsó sobre un botón (× o +)
                    let el = e.target;
                    while (el && el !== g) {
                        if (el.dataset && el.dataset.nodrag) return;
                        el = el.parentNode;
                    }
                    e.preventDefault();
                    const rp = adoState.renderParams;
                    const r  = document.getElementById('adoSvg').getBoundingClientRect();
                    const mmX = (e.clientX - r.left  - rp.dx) / rp.scale;
                    const mmY = (rp.H - (e.clientY - r.top) - rp.dy) / rp.scale;
                    adoPickerClose(); adoWallMenuClose();
                    adoPushUndo();
                    adoState.dragging = { key: m.key, offX: mmX - m.x, offY: mmY - m.y,
                                          origX: m.x, origY: m.y };
                });

                const fs  = Math.min(Math.max(sw*0.16, 14), 26);
                const fs2 = Math.max(fs * 0.65, 11);

                // Abreviatura de tablero: primera letra (H, F, Fb)
                const tableroBase = (slot.base || 'HIDRÓFUGO').trim().toUpperCase()
                    .normalize('NFD').replace(/[\u0300-\u036f]/g,''); // quitar acentos
                const tableroShort = tableroBase.startsWith('FIB') ? 'Fb'
                                   : tableroBase.startsWith('FEN') ? 'F'
                                   : tableroBase.charAt(0);
                const tableroFull  = (slot.base || 'HIDRÓFUGO').split(' ')[0];

                // Abreviatura de acabado: primeras 4 letras + punto
                const acabadoFull  = slot.acabado || '';
                const acabadoShort = acabadoFull.length > 4 ? acabadoFull.slice(0,4)+'.' : acabadoFull;

                // Cada línea tiene versión completa y corta
                const lines = [
                    { full: m.modulo,                    short: m.modulo,           size: fs,  weight: 700, color: col.text  },
                    { full: `${m.l}×${m.a}`,             short: `${m.l}×${m.a}`,   size: fs2, weight: 400, color: '#64748b' },
                    ...(slot.panelGrosor ? [{ full: `Carril ${slot.panelGrosor}mm${slot.conPanel !== false ? ' c/panel' : ''}`, short: slot.panelGrosor, size: fs2, weight: 400, color: '#94a3b8' }] : []),
                    { full: tableroFull,                 short: tableroShort,       size: fs2, weight: 400, color: '#94a3b8' },
                    ...(acabadoFull      ? [{ full: acabadoFull,  short: acabadoShort,  size: fs2, weight: 400, color: '#64748b' }] : []),
                ];

                // Si todas las líneas caben → versión completa; si no → versión corta
                const lineH    = fs2 * 1.35;
                const useShort = sh < lines.length * lineH + 8;

                const startY = sy + sh/2 - (lines.length - 1) * lineH / 2;
                lines.forEach((ln, i) => {
                    const t = document.createElementNS('http://www.w3.org/2000/svg','text');
                    Object.entries({ x:sx+sw/2, y:startY + i*lineH,
                        'text-anchor':'middle','dominant-baseline':'middle',
                        fill:ln.color,'font-size':ln.size,'font-weight':ln.weight,'font-family':'monospace' })
                        .forEach(([k,v]) => t.setAttribute(k,v));
                    t.textContent = useShort ? ln.short : ln.full;
                    g.appendChild(t);
                });

                // Botón rotar (↻) — esquina superior izquierda
                {
                    const rg = document.createElementNS('http://www.w3.org/2000/svg','g');
                    rg.style.cursor = 'pointer';
                    rg.dataset.nodrag = '1';
                    rg.addEventListener('mousedown', e => e.stopPropagation());
                    rg.addEventListener('click', e => {
                        e.stopPropagation();
                        adoPushUndo();
                        // Detectar vecinos ANTES de rotar
                        const hasW = adoHasNeighbor(m, 'W');
                        const hasE = adoHasNeighbor(m, 'E');
                        const hasS = adoHasNeighbor(m, 'S');
                        const hasN = adoHasNeighbor(m, 'N');
                        const oldL = m.l, oldA = m.a;
                        const cx = m.x + oldL / 2, cy = m.y + oldA / 2;
                        m.l = oldA; m.a = oldL;
                        // Anclar cara X: W > E > centro
                        if (hasW) {
                            // cara W queda fija en m.x — sin cambio
                        } else if (hasE) {
                            m.x = m.x + oldL - m.l; // cara E queda en misma posición
                        } else {
                            m.x = cx - m.l / 2;
                        }
                        // Anclar cara Y: S > N > centro
                        if (hasS) {
                            // cara S queda fija en m.y — sin cambio
                        } else if (hasN) {
                            m.y = m.y + oldA - m.a; // cara N queda en misma posición
                        } else {
                            m.y = cy - m.a / 2;
                        }
                        delete adoState.faceMap[m.key];
                        adoRender();
                    });
                    const rc = document.createElementNS('http://www.w3.org/2000/svg','circle');
                    Object.entries({ cx:sx+20, cy:sy+20, r:12,
                        fill:'rgba(99,102,241,0.2)', stroke:'rgba(99,102,241,0.6)','stroke-width':1.5 })
                        .forEach(([k,v]) => rc.setAttribute(k,v));
                    const rt = document.createElementNS('http://www.w3.org/2000/svg','text');
                    Object.entries({ x:sx+20, y:sy+20.5, 'text-anchor':'middle',
                        'dominant-baseline':'middle', fill:'#a5b4fc','font-size':15,'font-weight':700 })
                        .forEach(([k,v]) => rt.setAttribute(k,v));
                    rt.textContent = '↻';
                    rg.appendChild(rc); rg.appendChild(rt);
                    g.appendChild(rg);
                }

                // Botón eliminar (×) — solo si hay más de 1 módulo
                if (adoState.placed.length > 1) {
                    const rg = document.createElementNS('http://www.w3.org/2000/svg','g');
                    rg.style.cursor = 'pointer';
                    rg.dataset.nodrag = '1';
                    rg.addEventListener('mousedown', e => e.stopPropagation());
                    rg.addEventListener('click', e => { e.stopPropagation(); adoRemoveModule(m.key); });
                    const rc = document.createElementNS('http://www.w3.org/2000/svg','circle');
                    Object.entries({ cx:sx+sw-20, cy:sy+20, r:12,
                        fill:'rgba(239,68,68,0.25)', stroke:'rgba(239,68,68,0.6)','stroke-width':1.5 })
                        .forEach(([k,v]) => rc.setAttribute(k,v));
                    const rt = document.createElementNS('http://www.w3.org/2000/svg','text');
                    Object.entries({ x:sx+sw-20, y:sy+20, 'text-anchor':'middle',
                        'dominant-baseline':'middle', fill:'#fca5a5','font-size':15,'font-weight':700 })
                        .forEach(([k,v]) => rt.setAttribute(k,v));
                    rt.textContent = '×';
                    rg.appendChild(rc); rg.appendChild(rt);
                    g.appendChild(rg);
                }

                // Botones (+) solo en lados sin módulo vecino
                if (canAdd) {
                    [
                        { dir:'E', cx:sx+sw+PR+3, cy:sy+sh/2 },
                        { dir:'W', cx:sx-PR-3,    cy:sy+sh/2 },
                        { dir:'N', cx:sx+sw/2,    cy:sy-PR-3 },
                        { dir:'S', cx:sx+sw/2,    cy:sy+sh+PR+3 },
                    ].forEach(({ dir, cx, cy }) => {
                        if (adoHasNeighbor(m, dir)) return; // ya hay módulo en ese lado
                        const pg = document.createElementNS('http://www.w3.org/2000/svg','g');
                        pg.style.cursor = 'pointer';
                        pg.dataset.nodrag = '1';
                        pg.addEventListener('mousedown', e => e.stopPropagation());
                        pg.addEventListener('click', e => {
                            e.stopPropagation();
                            adoShowPicker(m.key, dir, cx, cy);
                        });
                        const pc = document.createElementNS('http://www.w3.org/2000/svg','circle');
                        Object.entries({ cx, cy, r:PR,
                            fill:'rgba(20,184,166,0.18)', stroke:'rgba(20,184,166,0.65)','stroke-width':2 })
                            .forEach(([k,v]) => pc.setAttribute(k,v));
                        const pt = document.createElementNS('http://www.w3.org/2000/svg','text');
                        Object.entries({ x:cx, y:cy, 'text-anchor':'middle',
                            'dominant-baseline':'middle', fill:'#5eead4','font-size':20,'font-weight':700 })
                            .forEach(([k,v]) => pt.setAttribute(k,v));
                        pt.textContent = '+';
                        pg.appendChild(pc); pg.appendChild(pt);
                        g.appendChild(pg);
                    });
                }

                svg.appendChild(g);
            });

            // ── Paredes compartidas — dos líneas independientes por cara ─────
            const OFS = 3; // desplazamiento px en SVG para separar las dos líneas
            adoGetWallPairs().forEach(w => {
                const sx1 = svgX(w.xA), sy1 = svgY(w.yA);
                const sx2 = svgX(w.xB), sy2 = svgY(w.yB);
                const midSx = (sx1+sx2)/2, midSy = (sy1+sy2)/2;

                // Coordenadas de cada línea (desplazadas hacia su módulo)
                let l1, l2;
                if (w.orient === 'V') {
                    // key1 cara E → izquierda; key2 cara W → derecha
                    l1 = { x1:sx1-OFS, y1:sy1, x2:sx2-OFS, y2:sy2 };
                    l2 = { x1:sx1+OFS, y1:sy1, x2:sx2+OFS, y2:sy2 };
                } else {
                    // key1 cara N → abajo SVG (+); key2 cara S → arriba SVG (-)
                    l1 = { x1:sx1, y1:sy1+OFS, x2:sx2, y2:sy2+OFS };
                    l2 = { x1:sx1, y1:sy1-OFS, x2:sx2, y2:sy2-OFS };
                }

                // Color por estado de cada cara
                const fm = adoState.faceMap;
                [[l1, w.key1, w.face1],[l2, w.key2, w.face2]].forEach(([coords, key, face]) => {
                    const st = (fm[key] || {})[face];
                    const color = st === 'cerrado' ? '#ef4444' : '#22c55e';
                    const lw    = st === 'cerrado' ? 2.5 : 2;
                    const line = document.createElementNS('http://www.w3.org/2000/svg','line');
                    const la = { ...coords, stroke:color, 'stroke-width':lw };
                    if (!st) la['stroke-dasharray'] = '5,3';
                    Object.entries(la).forEach(([k,v]) => line.setAttribute(k,v));
                    svg.appendChild(line);
                });

                // Área clicable en el centro de la pared
                const hit = document.createElementNS('http://www.w3.org/2000/svg','line');
                Object.entries({ x1:sx1, y1:sy1, x2:sx2, y2:sy2, stroke:'transparent','stroke-width':20 })
                    .forEach(([k,v]) => hit.setAttribute(k,v));
                hit.style.cursor = 'pointer';
                hit.addEventListener('click', e => { e.stopPropagation(); adoWallClick(w, midSx, midSy); });
                svg.appendChild(hit);
            });

            // ── Caras exteriores (sin módulo vecino) — default ROJO ───────────
            adoState.placed.forEach(m => {
                if (adoState.dragging && adoState.dragging.key === m.key) return;
                const fm = adoState.faceMap;
                const OFS = 2; // px interior para no solapar con borde del rect
                [
                    { face:'S', x1:svgX(m.x),     y1:svgY(m.y)+OFS,     x2:svgX(m.x+m.l), y2:svgY(m.y)+OFS     },
                    { face:'N', x1:svgX(m.x),     y1:svgY(m.y+m.a)-OFS, x2:svgX(m.x+m.l), y2:svgY(m.y+m.a)-OFS },
                    { face:'W', x1:svgX(m.x)+OFS,     y1:svgY(m.y+m.a), x2:svgX(m.x)+OFS,     y2:svgY(m.y)     },
                    { face:'E', x1:svgX(m.x+m.l)-OFS, y1:svgY(m.y+m.a), x2:svgX(m.x+m.l)-OFS, y2:svgY(m.y)     },
                ].forEach(({ face, x1, y1, x2, y2 }) => {
                    if (adoHasNeighbor(m, face)) return; // cara compartida: ya la maneja adoGetWallPairs
                    const st = (fm[m.key] || {})[face];
                    const eff = st !== undefined ? st : 'cerrado'; // exterior default = ROJO
                    const color = eff === 'cerrado' ? '#ef4444' : '#22c55e';
                    const ln = document.createElementNS('http://www.w3.org/2000/svg','line');
                    const la = { x1, y1, x2, y2, stroke:color, 'stroke-width':2.5 };
                    if (eff === 'abierto') la['stroke-dasharray'] = '5,3';
                    Object.entries(la).forEach(([k,v]) => ln.setAttribute(k,v));
                    svg.appendChild(ln);
                    const midX = (x1+x2)/2, midY = (y1+y2)/2;
                    const hitL = document.createElementNS('http://www.w3.org/2000/svg','line');
                    Object.entries({ x1, y1, x2, y2, stroke:'transparent','stroke-width':16 })
                        .forEach(([k,v]) => hitL.setAttribute(k,v));
                    hitL.style.cursor = 'pointer';
                    hitL.addEventListener('click', e => { e.stopPropagation(); adoExtFaceClick(m.key, face, midX, midY); });
                    svg.appendChild(hitL);
                });
            });

            // ── Cotas de cada módulo ──────────────────────────────────────────
            adoState.placed.forEach(m => {
                if (adoState.dragging && adoState.dragging.key === m.key) return;
                const sx = svgX(m.x),  sy = svgY(m.y + m.a);
                const sw = m.l * scale, sh = m.a * scale;

                // L — centrado horizontal, borde inferior interior (cara larga)
                _adoDimLabel(svg, sx + sw / 2, sy + sh - 13, `L: ${Math.round(m.l)}`, m.key, 'l', true, 0);

                // A — girado 90°, cara corta derecha interior
                _adoDimLabel(svg, sx + sw - 13, sy + sh / 2, `A: ${Math.round(m.a)}`, m.key, 'a', true, -90);

                // X/Y: desviación respecto al vecino más cercano (0 = perfectamente encajado)
                const EPS8 = 8;
                const wNbr = adoState.placed.find(q =>
                    q.key !== m.key &&
                    Math.abs((q.x + q.l) - (m.x - ADO_GAP)) < EPS8 &&
                    q.y < m.y + m.a - EPS8 && q.y + q.a > m.y + EPS8);
                const sNbr = adoState.placed.find(q =>
                    q.key !== m.key &&
                    Math.abs((q.y + q.a) - (m.y - ADO_GAP)) < EPS8 &&
                    q.x < m.x + m.l - EPS8 && q.x + q.l > m.x + EPS8);
                const snapX = wNbr ? Math.round(m.x - (wNbr.x + wNbr.l + ADO_GAP)) : Math.round(m.x - x0mm);
                const snapY = sNbr ? Math.round(m.y - (sNbr.y + sNbr.a + ADO_GAP)) : Math.round(m.y - y0mm);
                _adoDimLabel(svg, sx + 30,      sy + sh - 30, `X: ${snapX}`, m.key, 'x', true, 0);
                _adoDimLabel(svg, sx + sw - 30, sy + sh - 30, `Y: ${snapY}`, m.key, 'y', true, 0);
            });

            // ── Leyenda y subtítulo ──
            document.getElementById('adoSubtitle').textContent =
                `${adoState.placed.length} / ${adoState.pool.length} módulos colocados`;

            const typeTot = {}, typePlaced = {};
            adoState.pool.forEach(p => { typeTot[p.modulo] = (typeTot[p.modulo]||0)+1; });
            adoState.placed.forEach(p => { typePlaced[p.modulo] = (typePlaced[p.modulo]||0)+1; });

            document.getElementById('adoLegend').innerHTML =
                Object.entries(typeTot).map(([mod, tot]) => {
                    const done = typePlaced[mod] || 0;
                    const c = ADO_COLORS[mod] || ADO_COLORS['M1'];
                    return `<span style="display:inline-flex;align-items:center;gap:4px;">
                        <span style="display:inline-block;width:9px;height:9px;border-radius:2px;background:${c.fill};border:1px solid ${c.stroke};"></span>
                        <span style="color:${c.text};font-weight:700;">${mod}</span>
                        <span style="color:#475569;">${done}/${tot}</span>
                    </span>`;
                }).join('<span style="color:#1e293b;margin:0 6px;">│</span>') +
                (unplaced.length === 0
                    ? '<span style="margin-left:10px;color:#5eead4;font-weight:600;">✓ Todos colocados</span>'
                    : `<span style="margin-left:10px;color:#f59e0b;">${unplaced.length} sin colocar</span>`);
        }

        function adoShowPicker(targetKey, dir, svgCx, svgCy) {
            adoWallMenuClose();
            adoState.pending = { targetKey, dir };
            const unplaced = adoUnplaced();

            // Agrupar por tipo de módulo
            const byType = {};
            unplaced.forEach(p => { (byType[p.modulo] = byType[p.modulo]||[]).push(p); });

            document.getElementById('adoPickerList').innerHTML =
                Object.entries(byType).map(([mod, slots]) => {
                    const p = slots[0];
                    const c = ADO_COLORS[mod] || ADO_COLORS['M1'];
                    return `<button onclick="adoPickModule('${p.poolId}')"
                        style="display:block;width:100%;text-align:left;background:rgba(71,85,105,0.25);
                               border:1px solid #334155;border-radius:5px;padding:6px 10px;margin-bottom:5px;
                               cursor:pointer;color:#e2e8f0;font-size:12px;font-family:monospace;"
                        onmouseover="this.style.background='rgba(20,184,166,0.15)';this.style.borderColor='rgba(20,184,166,0.5)'"
                        onmouseout="this.style.background='rgba(71,85,105,0.25)';this.style.borderColor='#334155'">
                        <span style="font-weight:700;color:${c.text}">${mod}</span>
                        <span style="color:#64748b;"> ${p.l}×${p.a}</span>
                        <span style="float:right;color:#475569;font-size:11px;">×${slots.length}</span>
                    </button>`;
                }).join('');

            // Posicionar el picker cerca del botón (+) en coordenadas SVG→px
            const wrap = document.getElementById('adoCanvasWrap');
            const svg  = document.getElementById('adoSvg');
            const vb   = svg.getAttribute('viewBox').split(' ').map(Number);
            const sr   = svg.getBoundingClientRect();
            const wr   = wrap.getBoundingClientRect();
            const px   = (svgCx / vb[2]) * sr.width  + (sr.left - wr.left);
            const py   = (svgCy / vb[3]) * sr.height + (sr.top  - wr.top);

            const picker = document.getElementById('adoPicker');
            picker.style.display = 'block';
            picker.style.left = Math.min(px + 16, wrap.clientWidth - 200) + 'px';
            picker.style.top  = Math.max(py - 30, 5) + 'px';
        }

        function adoPickerClose() {
            document.getElementById('adoPicker').style.display = 'none';
            adoState.pending = null;
        }

        function adoPickModule(poolId) {
            if (!adoState.pending) return;
            const { targetKey, dir } = adoState.pending;
            const target = adoState.placed.find(p => p.key === targetKey);
            const slot   = adoState.pool.find(p => p.poolId === poolId);
            if (!target || !slot) return;
            // Guard: no permitir colocar un módulo que ya está en placed
            if (adoState.placed.some(p => p.poolId === poolId)) return;

            // Heredar orientación del módulo destino
            const targetPool = adoState.pool.find(p => p.poolId === target.poolId);
            const targetRotado = targetPool && target.l !== targetPool.l;
            const newL = targetRotado ? slot.a : slot.l;
            const newA = targetRotado ? slot.l : slot.a;

            let nx, ny;
            switch (dir) {
                case 'E': nx = target.x + target.l + ADO_GAP; ny = target.y; break;
                case 'W': nx = target.x - newL - ADO_GAP;     ny = target.y; break;
                case 'N': nx = target.x; ny = target.y + target.a + ADO_GAP; break;
                case 'S': nx = target.x; ny = target.y - newA - ADO_GAP;     break;
            }

            adoPushUndo();
            adoState.placed.push({
                key: 'k_' + Date.now() + '_' + Math.random().toString(36).slice(2),
                poolId: slot.poolId,
                modulo: slot.modulo,
                l: newL,
                a: newA,
                x: nx, y: ny,
            });
            adoPickerClose();
            adoRender();
        }

        function adoRemoveModule(key) {
            if (adoState.placed.length <= 1) return;
            adoPushUndo();
            adoState.placed = adoState.placed.filter(p => p.key !== key);
            delete adoState.faceMap[key];
            adoPickerClose();
            adoWallMenuClose();
            adoRender();
        }

        function adoSave() {
            pushToHistory();

            // Normalizar: desplazar para que minX=0, minY=0
            const minX = Math.min(...adoState.placed.map(p => p.x));
            const minY = Math.min(...adoState.placed.map(p => p.y));
            const config = {
                placed:  adoState.placed.map(p => ({ ...p, x: p.x - minX, y: p.y - minY })),
                faceMap: JSON.parse(JSON.stringify(adoState.faceMap)),
            };

            // Guardar en todas las filas del grupo (para que hasLayout funcione en cada una)
            const rowIds = adoState.grupoRowIds.length ? adoState.grupoRowIds : [adoState.rowId];
            rowIds.forEach(rid => {
                const r = orders.find(o => o.id === rid);
                if (r) r.adosamiento = JSON.parse(JSON.stringify(config));
            });
            if (!rowIds.length) { adoClose(); return; }

            saveList(false);
            adoClose();
            renderTable();
        }
        // ── Drag & drop ───────────────────────────────────────────────────────────
        function adoHasOverlapWith(m) {
            return adoState.placed.some(q => {
                if (q.key === m.key) return false;
                return m.x < q.x + q.l && m.x + m.l > q.x &&
                       m.y < q.y + q.a && m.y + m.a > q.y;
            });
        }

        // Calcula posición con snap magnético a aristas de otros módulos (+ ADO_GAP)
        // Devuelve también las guías de alineación activas
        function adoSnapPosition(m, rawX, rawY) {
            const SNAP = 80; // mm de radio de atracción
            let bestX = rawX, bestY = rawY, dxBest = SNAP, dyBest = SNAP;
            let guideX = null, guideY = null; // posición mm de la guía activa

            adoState.placed.forEach(q => {
                if (q.key === m.key) return;

                // X: candidatos de adjacencia (sin guía) + alineación de bordes (con guía)
                [
                    { v: q.x + q.l + ADO_GAP, g: null },   // a la derecha (adjacencia)
                    { v: q.x - m.l - ADO_GAP, g: null },   // a la izquierda (adjacencia)
                    { v: q.x,           g: q.x       },     // alinear borde izq
                    { v: q.x + q.l - m.l, g: q.x + q.l }, // alinear borde der
                ].forEach(({ v, g }) => {
                    const d = Math.abs(rawX - v);
                    if (d < dxBest) { dxBest = d; bestX = v; guideX = g; }
                });

                // Y: candidatos de adjacencia (sin guía) + alineación de bordes (con guía)
                [
                    { v: q.y + q.a + ADO_GAP, g: null },   // encima (adjacencia)
                    { v: q.y - m.a - ADO_GAP, g: null },   // debajo (adjacencia)
                    { v: q.y,           g: q.y       },     // alinear borde inferior
                    { v: q.y + q.a - m.a, g: q.y + q.a }, // alinear borde superior
                ].forEach(({ v, g }) => {
                    const d = Math.abs(rawY - v);
                    if (d < dyBest) { dyBest = d; bestY = v; guideY = g; }
                });
            });

            return { x: bestX, y: bestY, guideX, guideY };
        }

        function adoDragMove(e) {
            if (!adoState.dragging) return;
            const rp = adoState.renderParams;
            if (!rp) return;
            const r   = document.getElementById('adoSvg').getBoundingClientRect();
            const mmX = (e.clientX - r.left - rp.dx) / rp.scale;
            const mmY = (rp.H - (e.clientY - r.top) - rp.dy) / rp.scale;
            const rawX = mmX - adoState.dragging.offX;
            const rawY = mmY - adoState.dragging.offY;

            const p = adoState.placed.find(q => q.key === adoState.dragging.key);
            if (!p) return;

            const snapped = adoSnapPosition(p, rawX, rawY);
            p.x = snapped.x;
            p.y = snapped.y;
            adoState.dragging.guideX = snapped.guideX;
            adoState.dragging.guideY = snapped.guideY;

            // Detectar módulo sobre el que se está arrastrando (centro del módulo arrastrado dentro del bbox de otro)
            const cx = p.x + p.l / 2, cy = p.y + p.a / 2;
            const swapTarget = adoState.placed.find(q =>
                q.key !== p.key && cx > q.x && cx < q.x + q.l && cy > q.y && cy < q.y + q.a
            );
            adoState.dragging.swapTarget = swapTarget ? swapTarget.key : null;
            adoRender();
        }

        function adoDragEnd() {
            if (!adoState.dragging) return;
            const { key, origX, origY, swapTarget } = adoState.dragging;
            const p = adoState.placed.find(q => q.key === key);
            if (p) {
                if (swapTarget) {
                    // Intercambiar posiciones
                    const swapMod = adoState.placed.find(q => q.key === swapTarget);
                    if (swapMod) {
                        const sx = swapMod.x, sy = swapMod.y;
                        swapMod.x = origX; swapMod.y = origY;
                        p.x = sx;         p.y = sy;
                        // Limpiar faceMaps de ambos (adyacencia cambió)
                        delete adoState.faceMap[p.key];
                        delete adoState.faceMap[swapMod.key];
                    }
                } else if (adoHasOverlapWith(p)) {
                    // Solapamiento sin swap → revertir
                    p.x = origX;
                    p.y = origY;
                } else if (p.x !== origX || p.y !== origY) {
                    // Movido sin solapamiento → limpiar cara (adyacencia cambió)
                    delete adoState.faceMap[p.key];
                }
            }
            adoState.dragging = null;
            adoRender();
        }

        // ── Detectar vecino en una dirección ──────────────────────────────────────
        function adoHasNeighbor(m, dir) {
            const EPS = 8;
            return adoState.placed.some(q => {
                if (q.key === m.key) return false;
                const yOvlp = q.y < m.y + m.a - EPS && q.y + q.a > m.y + EPS;
                const xOvlp = q.x < m.x + m.l - EPS && q.x + q.l > m.x + EPS;
                switch (dir) {
                    case 'E': return Math.abs(q.x          - (m.x + m.l + ADO_GAP)) < EPS && yOvlp;
                    case 'W': return Math.abs((q.x + q.l)  - (m.x - ADO_GAP))       < EPS && yOvlp;
                    case 'N': return Math.abs(q.y          - (m.y + m.a + ADO_GAP)) < EPS && xOvlp;
                    case 'S': return Math.abs((q.y + q.a)  - (m.y - ADO_GAP))       < EPS && xOvlp;
                }
                return false;
            });
        }

        // ── Obtener todas las paredes compartidas ─────────────────────────────────
        function adoGetWallPairs() {
            const walls = [], EPS = 8, placed = adoState.placed;
            for (let i = 0; i < placed.length; i++) {
                for (let j = i+1; j < placed.length; j++) {
                    const a = placed[i], b = placed[j];
                    const yOvlp = Math.min(a.y+a.a, b.y+b.a) - Math.max(a.y, b.y);
                    const xOvlp = Math.min(a.x+a.l, b.x+b.l) - Math.max(a.x, b.x);
                    if (Math.abs(b.x - (a.x+a.l+ADO_GAP)) < EPS && yOvlp > EPS) {
                        // b al Este de a
                        const xM = a.x+a.l+ADO_GAP/2;
                        walls.push({ key1:a.key, key2:b.key, face1:'E', face2:'W', orient:'V',
                            xA:xM, yA:Math.max(a.y,b.y), xB:xM, yB:Math.min(a.y+a.a,b.y+b.a) });
                    } else if (Math.abs(a.x - (b.x+b.l+ADO_GAP)) < EPS && yOvlp > EPS) {
                        // a al Este de b
                        const xM = b.x+b.l+ADO_GAP/2;
                        walls.push({ key1:b.key, key2:a.key, face1:'E', face2:'W', orient:'V',
                            xA:xM, yA:Math.max(a.y,b.y), xB:xM, yB:Math.min(a.y+a.a,b.y+b.a) });
                    } else if (Math.abs(b.y - (a.y+a.a+ADO_GAP)) < EPS && xOvlp > EPS) {
                        // b al Norte de a
                        const yM = a.y+a.a+ADO_GAP/2;
                        walls.push({ key1:a.key, key2:b.key, face1:'N', face2:'S', orient:'H',
                            xA:Math.max(a.x,b.x), yA:yM, xB:Math.min(a.x+a.l,b.x+b.l), yB:yM });
                    } else if (Math.abs(a.y - (b.y+b.a+ADO_GAP)) < EPS && xOvlp > EPS) {
                        // a al Norte de b
                        const yM = b.y+b.a+ADO_GAP/2;
                        walls.push({ key1:b.key, key2:a.key, face1:'N', face2:'S', orient:'H',
                            xA:Math.max(a.x,b.x), yA:yM, xB:Math.min(a.x+a.l,b.x+b.l), yB:yM });
                    }
                }
            }
            return walls;
        }

        // ── Menú de pared — dos filas independientes ──────────────────────────────
        function adoWallClick(w, svgCx, svgCy) {
            adoPickerClose();
            adoState.pendingWall = w;
            const m1 = adoState.placed.find(p => p.key === w.key1);
            const m2 = adoState.placed.find(p => p.key === w.key2);
            const fm = adoState.faceMap;

            function faceRow(key, face, mod) {
                const st = (fm[key] || {})[face];
                const btnBase = 'border-radius:4px;padding:4px 7px;cursor:pointer;font-size:11px;font-weight:700;font-family:monospace;border:1px solid';
                const rBtn = (type, label, color, bg) =>
                    `<button onclick="adoSetFace('${key}','${face}','${type}')"
                        style="${btnBase} ${color};background:${bg};color:${color.replace('border:','')};
                        outline:${st===type?'2px solid '+color.split(';')[0].trim():'none'};outline-offset:1px;"
                        onmouseover="this.style.opacity='.8'" onmouseout="this.style.opacity='1'">${label}</button>`;
                const delBtn = st ? `<button onclick="adoSetFace('${key}','${face}',null)"
                        style="${btnBase} #334155;background:transparent;color:#64748b;"
                        onmouseover="this.style.opacity='.7'" onmouseout="this.style.opacity='1'">✕</button>` : '';
                return `<div style="margin-bottom:8px;">
                    <div style="font-size:10px;color:#94a3b8;margin-bottom:4px;">
                        <span style="font-weight:700;color:#e2e8f0;">${mod ? mod.modulo : '?'}</span>
                        &nbsp;cara&nbsp;<b>${face}</b>
                        ${st ? `&nbsp;<span style="color:${st==='cerrado'?'#ef4444':'#22c55e'}">${st.toUpperCase()}</span>` : '&nbsp;<span style="color:#22c55e">ABIERTO</span>'}
                    </div>
                    <div style="display:flex;gap:4px;flex-wrap:wrap;">
                        ${rBtn('cerrado','● CERRADO','#ef4444','rgba(239,68,68,0.12)')}
                        ${rBtn('abierto','● ABIERTO','#22c55e','rgba(34,197,94,0.12)')}
                        ${delBtn}
                    </div>
                </div>`;
            }

            document.getElementById('adoWallMenu').innerHTML =
                `<div style="font-size:10px;color:#64748b;margin-bottom:8px;text-transform:uppercase;letter-spacing:.06em;">Cara compartida</div>
                 ${faceRow(w.key1, w.face1, m1)}
                 ${faceRow(w.key2, w.face2, m2)}
                 <button onclick="adoWallMenuClose()" style="margin-top:4px;width:100%;background:transparent;border:1px solid #1e293b;border-radius:4px;color:#475569;font-size:11px;padding:4px;cursor:pointer;">Cerrar</button>`;

            // Posicionar cerca del clic
            const wrap = document.getElementById('adoCanvasWrap');
            const svg  = document.getElementById('adoSvg');
            const vb   = svg.getAttribute('viewBox').split(' ').map(Number);
            const sr   = svg.getBoundingClientRect();
            const wr   = wrap.getBoundingClientRect();
            const px   = (svgCx / vb[2]) * sr.width  + (sr.left - wr.left);
            const py   = (svgCy / vb[3]) * sr.height + (sr.top  - wr.top);
            const menu = document.getElementById('adoWallMenu');
            menu.style.display = 'block';
            menu.style.left = Math.min(px + 10, wrap.clientWidth - 220) + 'px';
            menu.style.top  = Math.max(py - 60, 5) + 'px';
        }

        function adoSetFace(key, face, type) {
            adoPushUndo();
            if (!adoState.faceMap[key]) adoState.faceMap[key] = {};
            if (type === null) delete adoState.faceMap[key][face];
            else               adoState.faceMap[key][face] = type;
            adoRender();
            // Re-abrir el menú con el estado actualizado
            if (adoState.pendingWall) {
                const w = adoState.pendingWall;
                const svg = document.getElementById('adoSvg');
                const vb  = svg.getAttribute('viewBox').split(' ').map(Number);
                const rp  = adoState.renderParams;
                const menu = document.getElementById('adoWallMenu');
                const wrap = document.getElementById('adoCanvasWrap');
                const m1 = adoState.placed.find(p => p.key === w.key1);
                const m2 = adoState.placed.find(p => p.key === w.key2);
                const fm = adoState.faceMap;
                function faceRow(k, f, mod) {
                    const st = (fm[k] || {})[f];
                    const btnBase = 'border-radius:4px;padding:4px 7px;cursor:pointer;font-size:11px;font-weight:700;font-family:monospace;border:1px solid';
                    const rBtn = (t, label, color, bg) =>
                        `<button onclick="adoSetFace('${k}','${f}','${t}')"
                            style="${btnBase} ${color};background:${bg};color:${color};
                            outline:${st===t?'2px solid '+color:'none'};outline-offset:1px;"
                            onmouseover="this.style.opacity='.8'" onmouseout="this.style.opacity='1'">${label}</button>`;
                    const delBtn = st ? `<button onclick="adoSetFace('${k}','${f}',null)"
                            style="${btnBase} #334155;background:transparent;color:#64748b;"
                            onmouseover="this.style.opacity='.7'" onmouseout="this.style.opacity='1'">✕</button>` : '';
                    return `<div style="margin-bottom:8px;">
                        <div style="font-size:10px;color:#94a3b8;margin-bottom:4px;">
                            <span style="font-weight:700;color:#e2e8f0;">${mod ? mod.modulo : '?'}</span>
                            &nbsp;cara&nbsp;<b>${f}</b>
                            ${st ? `&nbsp;<span style="color:${st==='cerrado'?'#ef4444':'#22c55e'}">${st.toUpperCase()}</span>` : '&nbsp;<span style="color:#22c55e">ABIERTO</span>'}
                        </div>
                        <div style="display:flex;gap:4px;flex-wrap:wrap;">
                            ${rBtn('cerrado','● CERRADO','#ef4444','rgba(239,68,68,0.12)')}
                            ${rBtn('abierto','● ABIERTO','#22c55e','rgba(34,197,94,0.12)')}
                            ${delBtn}
                        </div>
                    </div>`;
                }
                menu.innerHTML =
                    `<div style="font-size:10px;color:#64748b;margin-bottom:8px;text-transform:uppercase;letter-spacing:.06em;">Cara compartida</div>
                     ${faceRow(w.key1, w.face1, m1)}
                     ${faceRow(w.key2, w.face2, m2)}
                     <button onclick="adoWallMenuClose()" style="margin-top:4px;width:100%;background:transparent;border:1px solid #1e293b;border-radius:4px;color:#475569;font-size:11px;padding:4px;cursor:pointer;">Cerrar</button>`;
            } else if (adoState.pendingExtFace) {
                const { key, face, svgCx, svgCy } = adoState.pendingExtFace;
                _adoExtFaceMenuRender(key, face, svgCx, svgCy);
            }
        }

        function adoExtFaceClick(key, face, svgCx, svgCy) {
            adoPickerClose();
            adoWallMenuClose();
            adoState.pendingExtFace = { key, face, svgCx, svgCy };
            _adoExtFaceMenuRender(key, face, svgCx, svgCy);
        }

        function _adoExtFaceMenuRender(key, face, svgCx, svgCy) {
            const m = adoState.placed.find(p => p.key === key);
            if (!m) return;
            const st  = (adoState.faceMap[key] || {})[face];
            const eff = st !== undefined ? st : 'cerrado';
            const btnBase = 'border-radius:4px;padding:4px 7px;cursor:pointer;font-size:11px;font-weight:700;font-family:monospace;border:1px solid';
            const rBtn = (type, label, color, bg) =>
                `<button onclick="adoSetFace('${key}','${face}','${type}')"
                    style="${btnBase} ${color};background:${bg};color:${color};
                    outline:${eff===type?'2px solid '+color:'none'};outline-offset:1px;"
                    onmouseover="this.style.opacity='.8'" onmouseout="this.style.opacity='1'">${label}</button>`;
            const delBtn = st !== undefined
                ? `<button onclick="adoSetFace('${key}','${face}',null)"
                    style="${btnBase} #334155;background:transparent;color:#64748b;"
                    onmouseover="this.style.opacity='.7'" onmouseout="this.style.opacity='1'">✕ Reset</button>` : '';
            const menu = document.getElementById('adoWallMenu');
            menu.innerHTML =
                `<div style="font-size:10px;color:#64748b;margin-bottom:8px;text-transform:uppercase;letter-spacing:.06em;">Cara exterior</div>
                 <div style="margin-bottom:8px;">
                   <div style="font-size:10px;color:#94a3b8;margin-bottom:4px;">
                     <span style="font-weight:700;color:#e2e8f0;">${m.modulo}</span>&nbsp;cara&nbsp;<b>${face}</b>
                     &nbsp;<span style="color:${eff==='cerrado'?'#ef4444':'#22c55e'}">${eff.toUpperCase()}</span>
                   </div>
                   <div style="display:flex;gap:4px;flex-wrap:wrap;">
                     ${rBtn('cerrado','● CERRADO','#ef4444','rgba(239,68,68,0.12)')}
                     ${rBtn('abierto','● ABIERTO','#22c55e','rgba(34,197,94,0.12)')}
                     ${delBtn}
                   </div>
                 </div>
                 <button onclick="adoWallMenuClose()" style="margin-top:4px;width:100%;background:transparent;border:1px solid #1e293b;border-radius:4px;color:#475569;font-size:11px;padding:4px;cursor:pointer;">Cerrar</button>`;
            const wrap = document.getElementById('adoCanvasWrap');
            const svg  = document.getElementById('adoSvg');
            const vb   = svg.getAttribute('viewBox').split(' ').map(Number);
            const sr   = svg.getBoundingClientRect(), wr = wrap.getBoundingClientRect();
            const px   = (svgCx / vb[2]) * sr.width  + (sr.left - wr.left);
            const py   = (svgCy / vb[3]) * sr.height + (sr.top  - wr.top);
            menu.style.display = 'block';
            menu.style.left = Math.min(px + 10, wrap.clientWidth - 220) + 'px';
            menu.style.top  = Math.max(py - 60, 5) + 'px';
        }

        function adoWallMenuClose() {
            const m = document.getElementById('adoWallMenu');
            if (m) m.style.display = 'none';
            adoState.pendingWall = null;
            adoState.pendingExtFace = null;
        }

// ── Helpers de cotas SVG ─────────────────────────────────────────────────────
        function _adoDimLabel(svg, x, y, text, key, field, interior, rotate) {
            const val    = parseInt(text.replace(/.*:/,''));
            const charW  = 7, pad = 5;
            const tw     = text.length * charW + pad * 2, th = 16;
            const fillBg = interior ? 'rgba(0,0,0,0.45)' : '#0f172a';
            const stroke = interior ? 'rgba(255,255,255,0.08)' : '#334155';
            const color  = interior ? '#64748b' : '#475569';

            const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            if (rotate) g.setAttribute('transform', `rotate(${rotate},${x},${y})`);
            g.style.cursor = 'pointer';
            g.addEventListener('mousedown', e => e.stopPropagation());
            g.addEventListener('click', e => { e.stopPropagation(); adoDimEdit(key, field, val, x, y); });

            const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            Object.entries({ x: x - tw/2, y: y - th/2, width: tw, height: th,
                fill: fillBg, rx: 3, stroke, 'stroke-width': 0.8 })
                .forEach(([k,v]) => bg.setAttribute(k,v));

            const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            Object.entries({ x, y, 'text-anchor':'middle', 'dominant-baseline':'middle',
                fill: color, 'font-size': 11, 'font-weight': 600, 'font-family':'monospace' })
                .forEach(([k,v]) => t.setAttribute(k,v));
            t.textContent = text;

            g.appendChild(bg);
            g.appendChild(t);
            svg.appendChild(g);
        }

        function adoDimEdit(key, field, currentVal, svgCx, svgCy) {
            adoPickerClose();
            adoWallMenuClose();
            const existing = document.getElementById('adoDimEditor');
            if (existing) existing.remove();

            const wrap = document.getElementById('adoCanvasWrap');
            const svg  = document.getElementById('adoSvg');
            const vb   = svg.getAttribute('viewBox').split(' ').map(Number);
            const sr   = svg.getBoundingClientRect();
            const wr   = wrap.getBoundingClientRect();
            const px   = (svgCx / vb[2]) * sr.width  + (sr.left - wr.left);
            const py   = (svgCy / vb[3]) * sr.height + (sr.top  - wr.top);

            const labels = {
                l: '↔ Largo (L) mm',
                a: '↕ Ancho (A) mm',
                x: '→ Posición X mm',
                y: '↑ Posición Y mm',
            };
            const isDim = field === 'l' || field === 'a';

            const div = document.createElement('div');
            div.id = 'adoDimEditor';
            div.style.cssText = `position:absolute;z-index:30;background:#1e293b;
                border:1px solid ${isDim ? '#3b82f6' : '#f59e0b'};border-radius:8px;
                padding:10px 12px;box-shadow:0 8px 32px rgba(0,0,0,0.6);
                left:${Math.min(px - 60, wrap.clientWidth - 155)}px;
                top:${Math.max(py - 60, 5)}px;`;
            div.innerHTML = `
                <div style="font-size:10px;color:#64748b;margin-bottom:6px;
                            text-transform:uppercase;letter-spacing:.06em;">
                    ${labels[field]}
                </div>
                <div style="display:flex;gap:6px;align-items:center;">
                    <input id="adoDimInput" type="number" value="${currentVal}" step="1"
                        style="width:82px;background:#0f172a;
                               border:1px solid ${isDim ? '#3b82f6' : '#f59e0b'};
                               border-radius:5px;padding:5px 8px;color:#e2e8f0;
                               font-size:13px;font-family:monospace;outline:none;
                               -moz-appearance:textfield;">
                    <button onclick="adoDimApply('${key}','${field}')"
                        style="background:${isDim ? '#3b82f6' : '#f59e0b'};border:none;
                               border-radius:5px;color:#fff;font-size:13px;font-weight:700;
                               padding:5px 9px;cursor:pointer;">✓</button>
                    <button onclick="document.getElementById('adoDimEditor').remove()"
                        style="background:transparent;border:1px solid #334155;border-radius:5px;
                               color:#64748b;font-size:12px;padding:5px 7px;cursor:pointer;">✕</button>
                </div>`;
            wrap.appendChild(div);
            const inp = document.getElementById('adoDimInput');
            inp.focus(); inp.select();
            inp.addEventListener('keydown', e => {
                if (e.key === 'Enter')  adoDimApply(key, field);
                if (e.key === 'Escape') div.remove();
            });
        }

        function adoDimApply(key, field) {
            const inp = document.getElementById('adoDimInput');
            if (!inp) return;
            const val = parseInt(inp.value);
            const isDim = field === 'l' || field === 'a';
            if (isNaN(val) || (isDim && (val < 100 || val > 20000))) {
                inp.style.borderColor = '#ef4444';
                inp.focus();
                return;
            }
            const m = adoState.placed.find(p => p.key === key);
            if (!m) return;
            adoPushUndo();
            const EPS8 = 8;
            if (field === 'x') {
                const wNbr = adoState.placed.find(q =>
                    q.key !== m.key &&
                    Math.abs((q.x + q.l) - (m.x - ADO_GAP)) < EPS8 &&
                    q.y < m.y + m.a - EPS8 && q.y + q.a > m.y + EPS8);
                const base = wNbr ? wNbr.x + wNbr.l + ADO_GAP
                                  : ((adoState.renderParams && adoState.renderParams.x0mm) || 0);
                m.x = val + base;
            } else if (field === 'y') {
                const sNbr = adoState.placed.find(q =>
                    q.key !== m.key &&
                    Math.abs((q.y + q.a) - (m.y - ADO_GAP)) < EPS8 &&
                    q.x < m.x + m.l - EPS8 && q.x + q.l > m.x + EPS8);
                const base = sNbr ? sNbr.y + sNbr.a + ADO_GAP
                                  : ((adoState.renderParams && adoState.renderParams.y0mm) || 0);
                m.y = val + base;
            } else {
                m[field] = val;
            }
            if (isDim) delete adoState.faceMap[key];
            document.getElementById('adoDimEditor').remove();
            adoRender();
        }

        // ── Atajos de teclado Ctrl+Z / Ctrl+Y ─────────────────────────────────────
        document.addEventListener('keydown', function(e) {
            const modal = document.getElementById('adoModal');
            if (!modal || modal.style.display === 'none') return;
            if (e.ctrlKey && !e.shiftKey && e.key === 'z') { e.preventDefault(); adoUndo(); }
            if (e.ctrlKey && (e.key === 'y' || (e.shiftKey && e.key === 'z'))) { e.preventDefault(); adoRedo(); }
        });

// ════════════════════════════════════════════════════════════════════════════
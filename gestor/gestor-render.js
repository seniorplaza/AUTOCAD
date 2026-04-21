// ═══ RENDER FUNCTIONS ════════════════════════════════════════════════════════
        function renderHeaders() {
            const headerRow = document.getElementById('headerRow');
            headerRow.innerHTML = '';
            const cols = getColumns();

            // Colgroup: anchos fijos para alineación perfecta header/filas
            const colWidths = {
                fecha: 80, oferta: 90, numPedido: 70, cliente: 110, destino: 120,
                _bracket: 14,
                serie: 80, cantidad: 48, modulo: 52, conjunto: 44, l: 58, a: 58, h: 58,
                estructura: 110, cubierta: 80, correas: 100, panel: 72,
                base: 68, acabado: 72, suministro: 80, perfilado: 72,
                color: 110, extra: 100
            };
            const table = document.getElementById('ordersTable');
            const oldCg = table.querySelector('colgroup');
            if (oldCg) oldCg.remove();
            const cg = document.createElement('colgroup');
            cols.forEach(col => {
                const c = document.createElement('col');
                const w = colWidths[col.id] || 80;
                c.style.width = w + 'px';
                c.style.minWidth = w + 'px';
                cg.appendChild(c);
            });
            // action col
            const cAction = document.createElement('col');
            cAction.style.width = '90px';
            cg.appendChild(cAction);
            table.insertBefore(cg, table.firstChild);
            
            cols.forEach(col => {
                const th = document.createElement('th');

                if (col.id === '_bracket') {
                    th.style.cssText = 'width:14px;min-width:14px;max-width:14px;padding:0;';
                    headerRow.appendChild(th);
                    return;
                }

                if (col.id === 'conjunto') {
                    th.className = "uppercase text-center";
                    th.style.cssText = 'width:44px;min-width:44px;padding:4px 2px;font-size:10px;color:#64748b;';
                    th.textContent = 'Adj.';
                    headerRow.appendChild(th);
                    return;
                }

                th.className = "uppercase";
                
                // Filtro especial para fecha (rango de fechas)
                const filterContent = col.id === 'fecha' ? `
                    <div class="filter-row">
                        <div class="relative flex items-center w-full px-1">
                            <button id="dateRangeBtn" class="date-filter-btn ${filters.fechaDesde || filters.fechaHasta ? 'active' : ''}" onclick="openDateRangePicker(event)">
                                <span class="material-symbols-outlined text-sm">date_range</span>
                                <span id="dateRangeLabel">${getDateRangeLabel()}</span>
                            </button>
                        </div>
                    </div>
                ` : `
                    <div class="filter-row">
                        <div class="relative flex items-center w-full px-1">
                            <input type="text" class="filter-input" data-col="${col.id}" placeholder=" " oninput="handleFilter(event)">
                            <span id="clear-${col.id}" class="material-symbols-outlined text-[16px] clear-filter-btn" onclick="clearSingleFilter('${col.id}')">close</span>
                        </div>
                    </div>
                `;
                
                th.innerHTML = `
                    <div class="flex items-center justify-center gap-1">
                        <span>${col.label}</span>
                        <span class="material-symbols-outlined sort-menu-trigger text-sm" onclick="toggleSortMenu(event, '${col.id}')">expand_more</span>
                    </div>
                    <div id="sort-menu-${col.id}" class="sort-menu">
                        <div class="sort-option" onclick="applySort('${col.id}', 'asc')">
                            <span class="material-symbols-outlined text-sm">arrow_upward</span>
                            ${col.type === 'number' || col.type === 'number-text' ? 'Menor a mayor' : col.type === 'date' ? 'Más antiguo' : 'A - Z'}
                        </div>
                        <div class="sort-option" onclick="applySort('${col.id}', 'desc')">
                            <span class="material-symbols-outlined text-sm">arrow_downward</span>
                            ${col.type === 'number' || col.type === 'number-text' ? 'Mayor a menor' : col.type === 'date' ? 'Más reciente' : 'Z - A'}
                        </div>
                        ${col.id === 'destino' ? `
                        <div class="sort-option" onclick="sortByDistance()">
                            <span class="material-symbols-outlined text-sm">navigation</span>
                            Por distancia
                        </div>
                        ` : ''}
                    </div>
                    ${filterContent}
                `;
                headerRow.appendChild(th);
            });

            const thAction = document.createElement('th');
            thAction.className = "uppercase action-col";
            thAction.innerHTML = `
                <div class="flex items-center justify-center gap-2 group/header">
                    <button onclick="toggleSelectAll()" class="action-btn transition-all opacity-0 group-hover/header:opacity-100 hover:!opacity-100" title="Seleccionar todos">
                        <span class="material-symbols-outlined text-lg ${selectedRows.size > 0 ? 'text-blue-500' : ''}">${selectedRows.size > 0 ? 'check_circle' : 'radio_button_unchecked'}</span>
                    </button>
                    <span>Acciones</span>
                </div>
                <div class="filter-row">
                    <div class="flex justify-center w-full">
                        <div class="flex items-center bg-slate-900/50 p-1 rounded-lg border border-slate-700/50">
                            <div class="flex items-center px-1">
                                <div id="favFilterBtn" onclick="toggleFavFilter()" class="fav-filter-btn" title="Filtrar por favoritos">
                                    <span class="material-symbols-outlined text-[20px]">kid_star</span>
                                </div>
                            </div>
                            ${modoActual === 'pedidos' ? `
                            <div class="w-[1px] h-4 bg-slate-700"></div>
                            <div class="flex gap-1.5 px-2">
                                <div class="color-filter-dot bg-green-500" data-color="green" onclick="toggleColorFilter('green')" title="Filtrar verdes"></div>
                                <div class="color-filter-dot bg-yellow-500" data-color="yellow" onclick="toggleColorFilter('yellow')" title="Filtrar amarillos"></div>
                                <div class="color-filter-dot bg-orange-500" data-color="orange" onclick="toggleColorFilter('orange')" title="Filtrar naranjas"></div>
                                <div class="color-filter-dot bg-red-500" data-color="red" onclick="toggleColorFilter('red')" title="Filtrar rojos"></div>
                                <div class="color-filter-dot bg-blue-500" data-color="blue" onclick="toggleColorFilter('blue')" title="Filtrar azules"></div>
                                <div class="color-filter-dot bg-pink-500" data-color="pink" onclick="toggleColorFilter('pink')" title="Filtrar rosas"></div>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
            headerRow.appendChild(thAction);
            
            // Restaurar valores de filtros en los inputs
            restoreFilterValues();
        }
        
        function restoreFilterValues() {
            // Restaurar valores de filtros de texto en los inputs
            Object.keys(filters).forEach(key => {
                if (key !== 'favorite' && key !== 'folder' && key !== 'fechaDesde' && key !== 'fechaHasta') {
                    const input = document.querySelector(`.filter-input[data-col="${key}"]`);
                    if (input && filters[key]) {
                        input.value = filters[key];
                        const clearBtn = document.getElementById(`clear-${key}`);
                        if (clearBtn) {
                            clearBtn.classList.add('visible');
                        }
                    }
                }
            });
            
            // Actualizar estado de filtros de favoritos y colores
            updateActionFiltersUI();
        }

        function renderTable() {
            _correasCache.clear();
            const body = document.getElementById('tableBody');
            body.innerHTML = '';
            const _fragment = document.createDocumentFragment();
            
            let data = orders.filter(item => {
                if (filters.favorite && !item.favorite) return false;
                if (filters.folder && item.folder !== filters.folder) return false;
                
                // Filtro de rango de fechas
                if (filters.fechaDesde || filters.fechaHasta) {
                    // En modo ofertas, usar la fecha de la revisión; en modo pedidos, usar item.fecha
                    let fechaParaFiltrar = item.fecha;
                    if (modoActual === 'ofertas') {
                        fechaParaFiltrar = getFechaRev(item);
                    }
                    
                    const itemDate = parseDate(fechaParaFiltrar);
                    if (itemDate === 0) return false; // Sin fecha válida
                    
                    if (filters.fechaDesde) {
                        const desde = parseDate(filters.fechaDesde);
                        if (itemDate < desde) return false;
                    }
                    if (filters.fechaHasta) {
                        const hasta = parseDate(filters.fechaHasta);
                        if (itemDate > hasta) return false;
                    }
                }
                
                return Object.keys(filters).every(key => {
                    if (key === 'favorite' || key === 'folder' || key === 'fechaDesde' || key === 'fechaHasta') return true;
                    
                    // Filtros específicos para modo OFERTAS
                    if (modoActual === 'ofertas') {
                        // Filtro para ofertaNum (buscar en oferta)
                        if (key === 'ofertaNum') {
                            if (!filters[key]) return true;
                            const searchTerm = filters[key].toLowerCase();
                            const ofertaNum = getOfertaNumero(item.oferta).toLowerCase();
                            return ofertaNum.includes(searchTerm);
                        }
                        // Filtro para revision (buscar en el número de revisión)
                        if (key === 'revision') {
                            if (!filters[key]) return true;
                            const searchTerm = filters[key].toLowerCase();
                            const rev = item.revision || 0;
                            const revText = rev === 0 ? '-' : `REV ${rev}`;
                            return revText.toLowerCase().includes(searchTerm);
                        }
                        // Filtro para notasRev (buscar en las notas de la revisión actual)
                        if (key === 'notasRev') {
                            if (!filters[key]) return true;
                            const searchTerm = filters[key].toLowerCase();
                            const currentRev = item.revision || 0;
                            const nota = (item.notasRev && item.notasRev[currentRev]) || '';
                            return nota.toLowerCase().includes(searchTerm);
                        }
                    }
                    
                    // Para panel, buscar en panelGrosor y panelTipo
                    if (key === 'panel') {
                        if (!filters[key]) return true;
                        const searchTerm = filters[key].toLowerCase();
                        const grosor = String(item.panelGrosor || '').toLowerCase();
                        const tipo = String(item.panelTipo || '').toLowerCase();
                        return grosor.includes(searchTerm) || tipo.includes(searchTerm);
                    }
                    // Para correas, buscar en líneas calculadas y badges (DADO, REF)
                    if (key === 'correas') {
                        if (!filters[key]) return true;
                        const searchTerm = filters[key].toLowerCase();
                        const result = calcularCorreas(item.l, item.a, item.base, item.panelGrosor, item.cubierta);
                        if (!result) return false;
                        const lineasText = result.lineas.join(' ').toLowerCase();
                        const esPanel = (item.cubierta || '').toUpperCase().trim() === 'PANEL';
                        const esHormigonada = (item.base || '').toUpperCase().trim() === 'HORMIGONADA';
                        const tieneDado = !esPanel && (result.corner || esHormigonada);
                        const anchura = parseInt(item.a) || 0;
                        const tieneRef = anchura > 2500;
                        const badgesText = (tieneDado ? 'dado' : '') + (tieneRef ? ' ref' : '');
                        return lineasText.includes(searchTerm) || badgesText.includes(searchTerm);
                    }
                    // Para estructura, buscar en valores calculados
                    if (key === 'estructura') {
                        if (!filters[key]) return true;
                        const searchTerm = filters[key].toLowerCase();
                        const hBase = String(calcularHBase(item.l, item.a, item.base, item.panelGrosor, item.aislado)).toLowerCase();
                        const hCubierta = String(calcularHCubierta(item.l, item.a, item.base, item.panelGrosor, item.cubierta)).toLowerCase();
                        const pilar = String(calcularPilar(item.a, item.panelGrosor)).toLowerCase();
                        return hBase.includes(searchTerm) || hCubierta.includes(searchTerm) || pilar.includes(searchTerm);
                    }
                    return !filters[key] || String(item[key] || '').toLowerCase().includes(filters[key].toLowerCase());
                });
            });

            data.sort((a, b) => {
                let valA = a[currentSort.key] || '';
                let valB = b[currentSort.key] || '';
                
                // Para panel, combinar panelGrosor y panelTipo
                if (currentSort.key === 'panel') {
                    valA = (a.panelGrosor || '') + ' ' + (a.panelTipo || '');
                    valB = (b.panelGrosor || '') + ' ' + (b.panelTipo || '');
                }
                
                const colConfig = columns.find(c => c.id === currentSort.key);
                if (colConfig?.type === 'date') { valA = parseDate(valA); valB = parseDate(valB); }
                else if (colConfig?.type === 'number-text') { valA = extractNumber(valA); valB = extractNumber(valB); }
                else if (colConfig?.type === 'number') { valA = parseFloat(valA) || 0; valB = parseFloat(valB) || 0; }
                else { valA = String(valA).toLowerCase(); valB = String(valB).toLowerCase(); }
                if (valA < valB) return currentSort.direction === 'asc' ? -1 : 1;
                if (valA > valB) return currentSort.direction === 'asc' ? 1 : -1;
                return 0;
            });

            // Filtrar por tipoRegistro según el modo actual
            if (modoActual === 'ofertas') {
                data = data.filter(item => item.tipoRegistro === 1);
            } else {
                data = data.filter(item => item.tipoRegistro !== 1);
            }

            data.forEach((item, index) => {
                const folderClass = item.folder ? `row-${item.folder}` : '';
                const selectedClass = selectedRows.has(item.id) ? 'row-selected' : '';
                // Agrupación visual: si el anterior tiene la misma oferta/numPedido, marcar como módulo agrupado
                const prev = data[index - 1];
                const isGrouped = prev && prev.oferta === item.oferta && prev.numPedido === item.numPedido && item.modulo && item.modulo !== 'M1';
                const groupedClass = isGrouped ? 'modulo-grouped' : '';
                const row = document.createElement('tr');
                row.className = `group relative transition-colors table-row ${item.favorite ? 'favorite-row' : ''} ${folderClass} ${selectedClass} ${groupedClass}`;
                row.dataset.id = item.id;
                row.style.setProperty('--row-index', item.id % 10);

                // Renderizado diferente según el modo
                if (modoActual === 'ofertas') {
                    // MODO OFERTAS: Solo FECHA, OFERTA (sin OF), REV, CLIENTE, NOTAS
                    const currentRev = item.revision || 0;
                    const currentNota = (item.notasRev && item.notasRev[currentRev]) || '';
                    const revEstaHecha = isRevHecha(item);
                    
                    // Determinar clase de fila según estado de REV
                    let revClass = '';
                    if (currentRev > 0) {
                        revClass = revEstaHecha ? 'rev-hecha' : 'rev-pendiente';
                    }
                    const selectedClass = selectedRows.has(item.id) ? 'row-selected' : '';
                    row.className = `group relative transition-colors table-row ${item.favorite ? 'favorite-row' : ''} ${folderClass} ${revClass} ${selectedClass}`;

                    row.innerHTML = `
                        <td onclick="openDatepicker(event, ${item.id}, true)" class="p-3 text-xs text-center table-text cursor-pointer hover:bg-slate-700/50 transition-colors">${getFechaRev(item) || '-'}</td>
                        <td contenteditable="true" onblur="updateValue(${item.id}, 'oferta', 'OF ' + this.innerText)" class="p-3 text-center uppercase mono-col">
                            <span class="oferta-text">${getOfertaNumero(item.oferta)}</span>
                        </td>
                        <td class="p-2 text-xs text-center">
                            <select onchange="updateRevision(${item.id}, this.value)" class="select-card rev-select" style="min-width: 80px;">
                                <option value="0" ${currentRev === 0 ? 'selected' : ''}>-</option>
                                ${[1,2,3,4,5,6,7,8,9,10].map(rev => `
                                    <option value="${rev}" ${currentRev === rev ? 'selected' : ''}>REV ${rev}</option>
                                `).join('')}
                            </select>
                        </td>
                        <td contenteditable="true" onblur="updateValue(${item.id}, 'cliente', this.innerText)" class="p-3 text-sm font-semibold text-center cliente-text">${item.cliente || '-'}</td>
                        <td contenteditable="true" onblur="updateNotasRev(${item.id}, this.innerText)" class="p-3 italic text-xs text-center extra-text" title="${currentRev > 0 ? 'Nota para REV ' + currentRev : 'Nota general'}">${currentNota}</td>
                        <td class="p-3 text-center action-col">
                            <div class="flex items-center justify-center gap-3">
                                <!-- CHECKBOX DE SELECCIÓN (oculto hasta hover o seleccionado) -->
                                <button onclick="toggleRowSelection(${item.id})" class="action-btn transition-colors ${selectedRows.has(item.id) ? '' : 'opacity-0 group-hover:opacity-100'}" data-id="${item.id}">
                                    <span class="material-symbols-outlined text-lg ${selectedRows.has(item.id) ? 'text-blue-500' : ''}">${selectedRows.has(item.id) ? 'check_circle' : 'radio_button_unchecked'}</span>
                                </button>
                                <!-- ACCIONES EN HOVER (Izquierda) -->
                                <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 border-r border-slate-700 pr-3">
                                    <button onclick="toggleFavorite(${item.id})" class="action-btn transition-colors">
                                        <span class="material-symbols-outlined text-lg ${item.favorite ? 'star-active' : ''}">kid_star</span>
                                    </button>
                                    <button onclick="copyToClipboard(event, ${item.id})" class="action-btn transition-colors" title="Copiar al portapapeles">
                                        <span class="material-symbols-outlined text-lg">content_copy</span>
                                    </button>
                                    <button onclick="askDeleteRow(${item.id})" class="action-btn transition-colors">
                                        <span class="material-symbols-outlined text-lg">delete</span>
                                    </button>
                                </div>
                                
                                <!-- ICONO PEDIDO/OFERTA + SEPARADOR + CHECK REV -->
                                <div class="flex items-center">
                                    <button onclick="toggleTipoRegistro(${item.id})" class="action-btn transition-colors" title="${getTipoRegistroTitle(item.tipoRegistro || 0)}">
                                        <span class="material-symbols-outlined text-lg" style="color: ${getTipoRegistroColor(item.tipoRegistro || 0)}">${getTipoRegistroIcon(item.tipoRegistro || 0)}</span>
                                    </button>
                                    <!-- Separador sutil -->
                                    <div class="estado-separator"></div>
                                    <!-- Botón check REV hecha -->
                                    <button onclick="toggleRevHecha(${item.id})" class="action-btn transition-colors" title="${currentRev > 0 ? (revEstaHecha ? 'REV ' + currentRev + ' hecha - Clic para desmarcar' : 'Marcar REV ' + currentRev + ' como hecha') : 'Selecciona una REV primero'}">
                                        <span class="material-symbols-outlined text-lg" style="color: ${revEstaHecha ? '#22c55e' : '#ef4444'}">${revEstaHecha ? 'check_box' : 'check_box_outline_blank'}</span>
                                    </button>
                                </div>
                            </div>
                        </td>
                    `;
                } else {
                    // MODO PEDIDOS: Todas las columnas
                    // Calcular grupo: cuántos módulos tiene este mismo pedido en los datos visibles
                    const groupKey = (item.oferta || '') + '||' + (item.numPedido || '') + '||' + (item.cliente || '');
                    const groupItems = data.filter(d => 
                        (d.oferta || '') + '||' + (d.numPedido || '') + '||' + (d.cliente || '') === groupKey
                    );
                    const groupSize = groupItems.length;
                    const isFirstInGroup = groupItems[0].id === item.id;
                    const isGrouped = groupSize > 1;

                    const groupIndex = groupItems.findIndex(g => g.id === item.id);
                    const isFirst = groupIndex === 0;
                    const isLast  = groupIndex === groupSize - 1;

                    // Reglas de celdas por fila:
                    // - isFirstInGroup + isGrouped:   fecha..destino(rowspan) + bracket(rowspan+SVG)
                    // - isFirstInGroup + !isGrouped:  fecha..destino(rowspan=1) + bracket vacío(1td)
                    // - !isFirstInGroup:               nada (rowspan de la primera fila lo cubre)
                    let sharedCells = '';
                    if (isFirstInGroup) {
                        const bracketSvg = isGrouped ? `
                    <svg xmlns="http://www.w3.org/2000/svg" style="position:absolute;top:0;left:0;width:14px;height:100%;overflow:visible;pointer-events:none;">
                        <line x1="5" y1="${(0.5/groupSize*100).toFixed(2)}%" x2="5" y2="${((groupSize-0.5)/groupSize*100).toFixed(2)}%" stroke="#75FBFD" stroke-width="1.5" stroke-linecap="round"/>
                        ${Array.from({length: groupSize}, (_, gi) => {
                            const pct = ((gi + 0.5) / groupSize * 100).toFixed(2);
                            return `<line x1="5" y1="${pct}%" x2="14" y2="${pct}%" stroke="#75FBFD" stroke-width="1.5" stroke-linecap="round"/>`;
                        }).join('')}
                    </svg>` : '';
                        sharedCells = `
                    <td onclick="openDatepicker(event, ${item.id})" rowspan="${groupSize}" class="shared-cell p-3 text-xs text-center table-text cursor-pointer hover:bg-slate-700/50 transition-colors align-middle">${item.fecha || '-'}</td>
                    <td contenteditable="true" onblur="updateValue(${item.id}, 'oferta', 'OF ' + this.innerText)" rowspan="${groupSize}" class="shared-cell p-3 text-center uppercase mono-col align-middle">
                        <span class="oferta-text">${getOfertaNumero(item.oferta)}</span>
                    </td>
                    <td contenteditable="true" onblur="updateValue(${item.id}, 'numPedido', this.innerText)" rowspan="${groupSize}" class="shared-cell p-3 text-center uppercase mono-col align-middle">
                        <span class="text-purple-400 font-bold">${item.numPedido || '-'}</span>
                    </td>
                    <td contenteditable="true" onblur="updateValue(${item.id}, 'cliente', this.innerText)" rowspan="${groupSize}" class="shared-cell p-3 text-sm font-semibold text-center cliente-text align-middle">${item.cliente || '-'}</td>
                    <td contenteditable="true" onblur="updateValue(${item.id}, 'destino', this.innerText)" rowspan="${groupSize}" class="shared-cell p-3 text-xs text-center leading-tight destino-text align-middle">${item.destino || '-'}</td>
                    <td rowspan="${groupSize}" class="shared-cell" style="width:14px;min-width:14px;max-width:14px;padding:0;position:relative;">${bracketSvg}</td>`;
                    }

                    row.innerHTML = `
                    ${sharedCells}
                    <td contenteditable="true" onblur="updateValue(${item.id}, 'serie', this.innerText)" class="p-3 text-xs text-center mono-col serie-text">${item.serie || '-'}</td>
                    <td class="text-center" style="min-width:48px;vertical-align:middle;">
                        <input type="number" min="1" max="99" value="${item.cantidad || 1}" onchange="updateValue(${item.id}, 'cantidad', this.value)" style="width:36px;background:#1e293b;border:1px solid #475569;border-radius:4px;color:#e2e8f0;font-size:11px;font-weight:700;text-align:center;padding:2px 0;outline:none;display:block;margin:0 auto;-moz-appearance:textfield;" title="Cantidad" />
                    </td>
                    <td class="p-2 text-center" style="min-width:48px;">
                        <span onclick="cycleModulo(${item.id})" title="Clic para cambiar módulo" style="display:inline-block;padding:2px 7px;border-radius:5px;font-size:11px;font-weight:700;cursor:pointer;letter-spacing:0.03em;${getModuloStyle(item.modulo)}">${item.modulo || 'M1'}</span>
                    </td>
                    <td class="p-1 text-center" style="min-width:52px;vertical-align:middle;">
                        <div style="display:flex;flex-direction:column;align-items:center;gap:3px;">
                            <button onclick="toggleConjunto(${item.id})" title="${item.conjunto ? 'Módulo en CONJUNTO adosado — clic para cambiar a AISLADO' : 'Módulo AISLADO — clic para añadir a CONJUNTO adosado'}" style="display:inline-block;padding:2px 6px;border-radius:5px;font-size:10px;font-weight:700;cursor:pointer;letter-spacing:0.04em;${item.conjunto ? 'background:rgba(20,184,166,0.2);border:1px solid rgba(20,184,166,0.6);color:#5eead4;' : 'background:rgba(71,85,105,0.2);border:1px solid #475569;color:#64748b;'}">${item.conjunto ? 'CONJ' : 'AIS'}</button>
                            ${item.conjunto ? `<button onclick="toggleConjuntoVinculado(${item.id})" title="${item.conjuntoVinculado ? 'Vinculado — comparte configurador con las demás filas CONJ del pedido' : 'Independiente — tiene su propio configurador'}" style="width:18px;height:18px;border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center;padding:0;${item.conjuntoVinculado ? 'background:rgba(20,184,166,0.2);border:1px solid rgba(20,184,166,0.6);color:#5eead4;' : 'background:transparent;border:1px dashed #475569;color:#475569;'}"><span class="material-symbols-outlined" style="font-size:11px">${item.conjuntoVinculado ? 'link' : 'link_off'}</span></button>` : ''}
                        </div>
                    </td>
                    <td contenteditable="true" onblur="updateValue(${item.id}, 'l', this.innerText)" class="p-3 text-center text-emerald-400 font-bold mono-col separator-col">${item.l || '0'}</td>
                    <td contenteditable="true" onblur="updateValue(${item.id}, 'a', this.innerText)" class="p-3 text-center text-amber-400 font-bold mono-col separator-col">${item.a || '0'}</td>
                    <td contenteditable="true" onblur="updateValue(${item.id}, 'h', this.innerText)" class="p-3 text-center text-sky-400 font-bold mono-col">${item.h || '0'}</td>
                    <td class="p-2 text-xs text-center">
                        <div class="flex items-center justify-center gap-3">
                            <div class="flex items-center gap-1" title="H BASE - Altura de la base (calculado según L, A y Base)">
                                <span class="material-symbols-outlined" style="font-size: 20px; color: #ffffff; cursor: help;">vertical_align_bottom</span>
                                <span class="font-bold text-white" style="font-family: 'Courier New', monospace; font-size: 13px;">${calcularHBase(item.l, item.a, item.base, item.panelGrosor, item.aislado)}</span>
                            </div>
                            <div class="flex items-center gap-1" title="H CUBIERTA - Altura de la cubierta (calculado según L, A y Base)">
                                <span class="material-symbols-outlined" style="font-size: 20px; color: #ffffff; cursor: help;">vertical_align_top</span>
                                <span class="font-bold text-white" style="font-family: 'Courier New', monospace; font-size: 13px;">${calcularHCubierta(item.l, item.a, item.base, item.panelGrosor, item.cubierta)}</span>
                            </div>
                            <div class="flex items-center gap-1" title="PILAR - Dimensiones del pilar (calculado según A y grosor panel)">
                                <span class="material-symbols-outlined" style="font-size: 20px; color: #ffffff; cursor: help;">local_parking</span>
                                <span class="font-bold text-white" style="font-family: 'Courier New', monospace; font-size: 11px;">${calcularPilar(item.a, item.panelGrosor)}</span>
                            </div>
                        </div>
                    </td>
                    <td class="p-2 text-xs text-center">
                        <select onchange="updateCubierta(${item.id}, this.value)" class="select-card cubierta-select">
                            <option value="" ${!item.cubierta ? 'selected' : ''}>-</option>
                            <option value="ESTÁNDAR" ${item.cubierta === 'ESTÁNDAR' ? 'selected' : ''}>ESTÁNDAR</option>
                            <option value="PANEL" ${item.cubierta === 'PANEL' ? 'selected' : ''}>PANEL</option>
                        </select>
                    </td>
                    <td class="p-2 text-center" style="min-width:110px;">
                        ${renderCorreas(item.l, item.a, item.base, item.panelGrosor, item.cubierta)}
                    </td>
                    <td class="p-2 text-xs text-center">
                        <select onchange="updatePanelCombinado(${item.id}, this.value)" class="select-card panel-select">
                            <option value="" ${!item.panelGrosor && !item.panelTipo ? 'selected' : ''}>-</option>
                            <option disabled>──────────</option>
                            <optgroup label="30 mm">
                                <option value="30|PUR" ${item.panelGrosor === '30' && item.panelTipo === 'PUR' ? 'selected' : ''}>30 PUR</option>
                                <option value="30|PIR" ${item.panelGrosor === '30' && item.panelTipo === 'PIR' ? 'selected' : ''}>30 PIR</option>
                                <option value="30|LDR" ${item.panelGrosor === '30' && item.panelTipo === 'LDR' ? 'selected' : ''}>30 LDR</option>
                            </optgroup>
                            <option disabled>──────────</option>
                            <optgroup label="40 mm">
                                <option value="40|PUR" ${item.panelGrosor === '40' && item.panelTipo === 'PUR' ? 'selected' : ''}>40 PUR</option>
                                <option value="40|PIR" ${item.panelGrosor === '40' && item.panelTipo === 'PIR' ? 'selected' : ''}>40 PIR</option>
                                <option value="40|LDR" ${item.panelGrosor === '40' && item.panelTipo === 'LDR' ? 'selected' : ''}>40 LDR</option>
                            </optgroup>
                            <option disabled>──────────</option>
                            <optgroup label="50 mm">
                                <option value="50|PUR" ${item.panelGrosor === '50' && item.panelTipo === 'PUR' ? 'selected' : ''}>50 PUR</option>
                                <option value="50|PIR" ${item.panelGrosor === '50' && item.panelTipo === 'PIR' ? 'selected' : ''}>50 PIR</option>
                                <option value="50|LDR" ${item.panelGrosor === '50' && item.panelTipo === 'LDR' ? 'selected' : ''}>50 LDR</option>
                            </optgroup>
                            <option disabled>──────────</option>
                            <optgroup label="60 mm">
                                <option value="60|PUR" ${item.panelGrosor === '60' && item.panelTipo === 'PUR' ? 'selected' : ''}>60 PUR</option>
                                <option value="60|PIR" ${item.panelGrosor === '60' && item.panelTipo === 'PIR' ? 'selected' : ''}>60 PIR</option>
                                <option value="60|LDR" ${item.panelGrosor === '60' && item.panelTipo === 'LDR' ? 'selected' : ''}>60 LDR</option>
                            </optgroup>
                            <option disabled>──────────</option>
                            <optgroup label="80 mm">
                                <option value="80|PUR" ${item.panelGrosor === '80' && item.panelTipo === 'PUR' ? 'selected' : ''}>80 PUR</option>
                                <option value="80|PIR" ${item.panelGrosor === '80' && item.panelTipo === 'PIR' ? 'selected' : ''}>80 PIR</option>
                                <option value="80|LDR" ${item.panelGrosor === '80' && item.panelTipo === 'LDR' ? 'selected' : ''}>80 LDR</option>
                            </optgroup>
                            <option disabled>──────────</option>
                            <optgroup label="100 mm">
                                <option value="100|PUR" ${item.panelGrosor === '100' && item.panelTipo === 'PUR' ? 'selected' : ''}>100 PUR</option>
                                <option value="100|PIR" ${item.panelGrosor === '100' && item.panelTipo === 'PIR' ? 'selected' : ''}>100 PIR</option>
                                <option value="100|LDR" ${item.panelGrosor === '100' && item.panelTipo === 'LDR' ? 'selected' : ''}>100 LDR</option>
                            </optgroup>
                        </select>
                        ${item.panelGrosor ? `<label class="flex items-center gap-1 mt-1 cursor-pointer justify-center" style="font-size:10px; color:${item.conPanel === false ? '#f87171' : '#86efac'};">
                            <input type="checkbox" ${item.conPanel !== false ? 'checked' : ''} onchange="updateConPanel(${item.id}, this.checked)" style="cursor:pointer; accent-color:#22c55e;">
                            C/PANEL
                        </label>` : ''}
                    </td>
                    <td class="p-2 text-xs text-center base-text">
                        <select onchange="updateValue(${item.id}, 'base', this.value)" class="select-card base-select">
                            <option value="" ${!item.base ? 'selected' : ''}>-</option>
                            <option value="HIDRÓFUGO" ${item.base === 'HIDRÓFUGO' ? 'selected' : ''}>HIDRÓFUGO</option>
                            <option value="FENÓLICO" ${item.base === 'FENÓLICO' ? 'selected' : ''}>FENÓLICO</option>
                            <option value="HORMIGONADA" ${item.base === 'HORMIGONADA' ? 'selected' : ''}>HORMIGONADA</option>
                            <option value="FIBROCEMENTO" ${item.base === 'FIBROCEMENTO' ? 'selected' : ''}>FIBROCEMENTO</option>
                            <option value="TRAMEX" ${item.base === 'TRAMEX' ? 'selected' : ''}>TRAMEX</option>
                            <option value="SANEAMIENTO" ${item.base === 'SANEAMIENTO' ? 'selected' : ''}>SANEAMIENTO</option>
                            <option value="NO INCLUYE" ${item.base === 'NO INCLUYE' ? 'selected' : ''}>NO INCLUYE</option>
                            <option value="OTRO" ${item.base === 'OTRO' ? 'selected' : ''}>OTRO</option>
                        </select>
                        <label class="flex items-center gap-1 mt-1 cursor-pointer justify-center" style="font-size:10px; color:#aaa;">
                            <input type="checkbox" ${item.aislado ? 'checked' : ''} onchange="updateAislado(${item.id}, this.checked)" style="cursor:pointer; accent-color:#f59e0b;">
                            AISL.
                        </label>
                    </td>
                    <td class="p-2 text-xs text-center acabado-text">
                        <select onchange="updateValue(${item.id}, 'acabado', this.value)" class="select-card acabado-select">
                            <option value="" ${!item.acabado ? 'selected' : ''}>-</option>
                            <option value="SINTASOL" ${item.acabado === 'SINTASOL' ? 'selected' : ''}>SINTASOL</option>
                            <option value="TARKETT" ${item.acabado === 'TARKETT' ? 'selected' : ''}>TARKETT</option>
                            <option value="TARIMA" ${item.acabado === 'TARIMA' ? 'selected' : ''}>TARIMA</option>
                            <option value="PORCELÁNICO" ${item.acabado === 'PORCELÁNICO' ? 'selected' : ''}>PORCELÁNICO</option>
                            <option value="OTRO" ${item.acabado === 'OTRO' ? 'selected' : ''}>OTRO</option>
                        </select>
                    </td>
                    <td class="p-2 text-xs text-center suministro-text">
                        <select onchange="updateValue(${item.id}, 'suministro', this.value)" class="select-card suministro-select">
                            <option value="" ${!item.suministro ? 'selected' : ''}>-</option>
                            <option value="ARMADO" ${item.suministro === 'ARMADO' ? 'selected' : ''}>ARMADO</option>
                            <option value="KIT" ${item.suministro === 'KIT' ? 'selected' : ''}>KIT${item.suministro === 'KIT' ? ` | ${kitVariant(item)}` : ''}</option>
                            <option value="MECANO" ${item.suministro === 'MECANO' ? 'selected' : ''}>MECANO</option>
                        </select>
                    </td>
                    <td class="p-2 text-xs text-center">
                        <div class="perfilado-selector">
                            <button class="perfilado-button" onclick="togglePerfiladoMenu(event, ${item.id})">
                                ${item.perfilado || '-'}
                            </button>
                            <div id="perfilado-menu-${item.id}" class="perfilado-menu">
                                <div class="perfilado-option" onclick="setPerfilado(${item.id}, '')">
                                    <div class="perfilado-option-content">
                                        <div class="perfilado-label">-</div>
                                    </div>
                                </div>
                                <div class="perfilado-option" onclick="setPerfilado(${item.id}, 'GOF')">
                                    <div class="perfilado-option-content">
                                        <div class="perfilado-label">GOF</div>
                                        <span style="color: #64748b; font-size: 11px;">(Sin imagen)</span>
                                    </div>
                                </div>
                                ${['GL', 'GM', 'GN', 'GP1', 'GV', 'GW'].map(type => `
                                    <div class="perfilado-option" onclick="setPerfilado(${item.id}, '${type}')">
                                        <div class="perfilado-option-content">
                                            <img src="${perfiladoImages[type]}" class="perfilado-image" alt="${type}">
                                            <div class="perfilado-label">${type}</div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </td>
                    <td class="p-2 text-center">
                        <div class="flex items-center justify-center gap-2">
                            <div class="relative">
                                <div class="color-circle" style="background-color: ${item.colorPanel || '#94a3b8'}; color: ${getContrastColor(item.colorPanel || '#94a3b8')}" onclick="toggleColorMenu(event, ${item.id}, 'panel')" title="Panel">P</div>
                                <div id="color-menu-${item.id}-panel" class="color-menu"></div>
                            </div>
                            <div class="relative">
                                <div class="color-circle" style="background-color: ${item.colorEstructura || '#94a3b8'}; color: ${getContrastColor(item.colorEstructura || '#94a3b8')}" onclick="toggleColorMenu(event, ${item.id}, 'estructura')" title="Estructura">E</div>
                                <div id="color-menu-${item.id}-estructura" class="color-menu"></div>
                            </div>
                            <div class="relative">
                                <div class="color-circle" style="background-color: ${item.colorCarpinteria || '#94a3b8'}; color: ${getContrastColor(item.colorCarpinteria || '#94a3b8')}" onclick="toggleColorMenu(event, ${item.id}, 'carpinteria')" title="Carpintería">C</div>
                                <div id="color-menu-${item.id}-carpinteria" class="color-menu"></div>
                            </div>
                        </div>
                    </td>
                    <td contenteditable="true" onblur="updateValue(${item.id}, 'extra', this.innerText)" class="p-3 italic text-xs text-center extra-text">${item.extra || ''}</td>
                    <td class="p-3 text-center action-col">
                        <div class="flex items-center justify-center gap-3">
                            <!-- CHECKBOX DE SELECCIÓN (oculto hasta hover o seleccionado) -->
                            <button onclick="toggleRowSelection(${item.id})" class="action-btn transition-colors ${selectedRows.has(item.id) ? '' : 'opacity-0 group-hover:opacity-100'}" data-id="${item.id}">
                                <span class="material-symbols-outlined text-lg ${selectedRows.has(item.id) ? 'text-blue-500' : ''}">${selectedRows.has(item.id) ? 'check_circle' : 'radio_button_unchecked'}</span>
                            </button>
                            <!-- ACCIONES EN HOVER (Izquierda) -->
                            <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 border-r border-slate-700 pr-3">
                                <div class="relative">
                                    <button onclick="toggleFolderMenu(event, ${item.id})" class="action-btn transition-colors">
                                        <span class="material-symbols-outlined text-lg" style="color: ${getFolderColor(item.folder)}">folder_open</span>
                                    </button>
                                    <div id="folder-menu-${item.id}" class="folder-menu">
                                        <span class="material-symbols-outlined folder-option text-green-500" onclick="setFolder(${item.id}, 'green')">folder</span>
                                        <span class="material-symbols-outlined folder-option text-yellow-500" onclick="setFolder(${item.id}, 'yellow')">folder</span>
                                        <span class="material-symbols-outlined folder-option text-orange-500" onclick="setFolder(${item.id}, 'orange')">folder</span>
                                        <span class="material-symbols-outlined folder-option text-red-500" onclick="setFolder(${item.id}, 'red')">folder</span>
                                        <span class="material-symbols-outlined folder-option" style="color: #1886ed;" onclick="setFolder(${item.id}, 'blue')">folder</span>
                                        <span class="material-symbols-outlined folder-option" style="color: #e30052;" onclick="setFolder(${item.id}, 'pink')">folder</span>

                                        <span class="material-symbols-outlined folder-option text-slate-500" onclick="setFolder(${item.id}, null)">folder</span>
                                    </div>
                                </div>
                                <button onclick="toggleFavorite(${item.id})" class="action-btn transition-colors">
                                    <span class="material-symbols-outlined text-lg ${item.favorite ? 'star-active' : ''}">kid_star</span>
                                </button>
                                <button onclick="duplicateRow(${item.id})" class="action-btn transition-colors" title="Duplicar como nuevo módulo">
                                    <span class="material-symbols-outlined text-lg">add_box</span>
                                </button>
                                <button onclick="copyToClipboard(event, ${item.id})" class="action-btn transition-colors" title="Copiar al portapapeles">
                                    <span class="material-symbols-outlined text-lg">content_copy</span>
                                </button>
                                <button onclick="openPedidoFolder(${item.id})" class="action-btn transition-colors" title="Abrir pedido">
                                    <span class="material-symbols-outlined text-lg">folder_eye</span>
                                </button>
                                <button onclick="askDeleteRow(${item.id})" class="action-btn transition-colors">
                                    <span class="material-symbols-outlined text-lg">delete</span>
                                </button>
                            </div>
                            
                            <!-- ESTADOS SIEMPRE VISIBLES (Derecha) -->
                            <div class="flex items-center gap-2">
                                <button onclick="togglePrinted(${item.id})" class="action-btn transition-colors" title="${getPrintedTitle(item.printed)}">
                                    <span class="material-symbols-outlined text-lg ${getPrintedColor(item.printed)}">${getPrintedIcon(item.printed)}</span>
                                </button>
                                <button onclick="toggleSent(${item.id})" class="action-btn transition-colors" title="${getSentTitle(item.sent)}">
                                    <span class="material-symbols-outlined text-lg ${getSentColor(item.sent)}">${getSentIcon(item.sent)}</span>
                                </button>
                                <button onclick="toggleDelivered(${item.id})" class="action-btn transition-colors" title="${getDeliveredTitle(item.delivered)}">
                                    <span class="material-symbols-outlined text-lg ${getDeliveredColor(item.delivered)}">${getDeliveredIcon(item.delivered)}</span>
                                </button>
                                <!-- Separador sutil -->
                                <div class="estado-separator"></div>
                                <!-- Icono PEDIDO/OFERTA -->
                                <button onclick="toggleTipoRegistro(${item.id})" class="action-btn transition-colors" title="${getTipoRegistroTitle(item.tipoRegistro || 0)}">
                                    <span class="material-symbols-outlined text-lg" style="color: ${getTipoRegistroColor(item.tipoRegistro || 0)}">${getTipoRegistroIcon(item.tipoRegistro || 0)}</span>
                                </button>
                                ${item.conjunto ? (() => {
                                    const hasLayout = !!item.adosamiento;
                                    return `<div class="estado-separator"></div>
                                <button onclick="openAdosamientoConfig(${item.id})" class="action-btn transition-colors" title="${hasLayout ? 'Editar layout de adosamiento' : 'Configurar adosamiento'}">
                                    <span class="material-symbols-outlined text-lg" style="color:${hasLayout ? '#5eead4' : '#94a3b8'}">grid_view</span>
                                </button>`;
                                })() : ''}
                            </div>
                        </div>
                    </td>
                `;
                } // Fin del else (modo pedidos)
                _fragment.appendChild(row);
            });
            body.appendChild(_fragment);
            document.getElementById('count').innerText = data.length;
            document.getElementById('countLabel').innerText = modoActual === 'ofertas' ? 'ofertas' : 'pedidos';
            updateFilterStatus();
            updateActionFiltersUI();
            updateSelectionUI();
            
            // Enfocar celda pendiente si hay navegación con Enter
            focusPendingCell();

        }


// ═══ PRINT TO PDF ═══════════════════════════════════════════════════════════
        function printSelectedToPDF() {
            let pedidosImprimir = [];

            if (selectedRows.size > 0) {
                // Para cada ID seleccionado, expandir a todos sus módulos hermanos
                const idsExpandidos = new Set();
                selectedRows.forEach(id => {
                    const source = orders.find(o => o.id === id);
                    if (!source) return;
                    orders.filter(o =>
                        (o.oferta||'').trim() === (source.oferta||'').trim() &&
                        (o.numPedido||'').trim() === (source.numPedido||'').trim() &&
                        (o.cliente||'').trim() === (source.cliente||'').trim()
                    ).forEach(o => idsExpandidos.add(o.id));
                });
                // Recoger en orden: primero los visibles en tabla, luego los hermanos no visibles
                const visibleIds = Array.from(document.querySelectorAll('tr[data-id]')).map(r => parseInt(r.dataset.id));
                // Mantener orden de aparición
                idsExpandidos.forEach(id => {
                    const order = orders.find(o => o.id === id);
                    if (order) pedidosImprimir.push(order);
                });
                // Ordenar por orden de aparición en la tabla (visibles primero, en su orden)
                pedidosImprimir.sort((a, b) => {
                    const ai = visibleIds.indexOf(a.id);
                    const bi = visibleIds.indexOf(b.id);
                    if (ai === -1 && bi === -1) return 0;
                    if (ai === -1) return 1;
                    if (bi === -1) return -1;
                    return ai - bi;
                });
            } else {
                // Sin selección: imprimir todos los visibles + sus hermanos no visibles
                const visibleRows = document.querySelectorAll('tr[data-id]');
                const idsExpandidos = new Set();
                visibleRows.forEach(row => {
                    const id = parseInt(row.dataset.id);
                    const source = orders.find(o => o.id === id);
                    if (!source) return;
                    orders.filter(o =>
                        (o.oferta||'').trim() === (source.oferta||'').trim() &&
                        (o.numPedido||'').trim() === (source.numPedido||'').trim() &&
                        (o.cliente||'').trim() === (source.cliente||'').trim()
                    ).forEach(o => idsExpandidos.add(o.id));
                });
                const visibleIds = Array.from(visibleRows).map(r => parseInt(r.dataset.id));
                idsExpandidos.forEach(id => {
                    const order = orders.find(o => o.id === id);
                    if (order) pedidosImprimir.push(order);
                });
                pedidosImprimir.sort((a, b) => {
                    const ai = visibleIds.indexOf(a.id);
                    const bi = visibleIds.indexOf(b.id);
                    if (ai === -1 && bi === -1) return (a.modulo||'').localeCompare(b.modulo||'');
                    if (ai === -1) return 1;
                    if (bi === -1) return -1;
                    return ai - bi;
                });
            }
            
            if (pedidosImprimir.length === 0) {
                alert('No hay pedidos para imprimir');
                return;
            }
            
            const getFolderColorPrint = (type) => {
                const colors = { 'green': '#22c55e', 'yellow': '#eab308', 'orange': '#f97316', 'red': '#ef4444', 'blue': '#1886ed', 'pink': '#e30052' };
                return colors[type] || '#cccccc';
            };
            
            // Agrupar pedidos por oferta+numPedido+cliente (misma lógica que la tabla)
            // Un grupo = mismo pedido con múltiples módulos
            const grupos = [];
            const seenKeys = new Set();
            pedidosImprimir.forEach(p => {
                // Clave sin módulo: agrupa M1+M2+... del mismo pedido
                const key = (p.oferta||'').trim()+'||'+(p.numPedido||'').trim()+'||'+(p.cliente||'').trim();
                if (!seenKeys.has(key)) {
                    seenKeys.add(key);
                    const grupo = pedidosImprimir.filter(x =>
                        (x.oferta||'').trim()+'||'+(x.numPedido||'').trim()+'||'+(x.cliente||'').trim() === key
                    );
                    // Ordenar por módulo: M1, M2, M3...
                    grupo.sort((a,b) => (a.modulo||'M1').localeCompare(b.modulo||'M1'));
                    grupos.push(grupo);
                }
            });

            const rowsHtml = grupos.map(grupo => {
                const groupSize = grupo.length;
                const first = grupo[0];
                const folderColor = getFolderColorPrint(first.folder);
                const isGrouped = groupSize > 1;

                return grupo.map((p, gi) => {
                    const isFirst = gi === 0;
                    const isLast  = gi === groupSize - 1;
                    const estructura = `${calcularHBase(p.l, p.a, p.base, p.panelGrosor, p.aislado)}/${calcularHCubierta(p.l, p.a, p.base, p.panelGrosor, p.cubierta)}/${calcularPilar(p.a, p.panelGrosor)}`;
                    const panel = (p.panelGrosor || '') + (p.panelTipo ? ' ' + p.panelTipo : '') || '-';

                    // Corchete CSS puro (se imprime siempre, sin SVG)
                    const bTop    = isGrouped && isFirst  ? 'border-top:2px solid #06b6d4;'    : '';
                    const bBottom = isGrouped && isLast   ? 'border-bottom:2px solid #06b6d4;' : '';
                    const bLeft   = isGrouped             ? 'border-left:2px solid #06b6d4;'   : '';
                    const bracketStyle = `${bTop}${bBottom}${bLeft}-webkit-print-color-adjust:exact;print-color-adjust:exact;width:6px;padding:0;`;

                    const sharedCells = isFirst ? `
                        <td rowspan="${groupSize}"><span class="folder-dot" style="background-color:${folderColor};-webkit-print-color-adjust:exact;print-color-adjust:exact;"></span></td>
                        <td rowspan="${groupSize}">${first.fecha || '-'}</td>
                        <td rowspan="${groupSize}">${first.oferta || '-'}</td>
                        <td rowspan="${groupSize}">${first.numPedido || '-'}</td>
                        <td rowspan="${groupSize}" style="text-align:left;font-weight:bold;">${first.cliente || '-'}</td>
                        <td rowspan="${groupSize}" style="text-align:left;">${first.destino || '-'}</td>` : '';

                    return `
                    <tr>
                        ${sharedCells}
                        <td style="${bracketStyle}"></td>
                        <td style="font-weight:bold;color:#6366f1;-webkit-print-color-adjust:exact;print-color-adjust:exact;">${p.modulo || 'M1'}</td>
                        <td>${p.serie || '-'}</td>
                        <td>${p.cantidad || 1}</td>
                        <td>${p.l || '-'}</td>
                        <td>${p.a || '-'}</td>
                        <td>${p.h || '-'}</td>
                        <td>${estructura}</td>
                        <td>${panel}</td>
                        <td>${p.base || '-'}</td>
                        <td>${p.acabado || '-'}</td>
                        <td>${p.suministro || '-'}</td>
                        <td>${p.perfilado || '-'}</td>
                        <td style="font-size:7px;">P:${p.colorPanel||'-'} E:${p.colorEstructura||'-'} C:${p.colorCarpinteria||'-'}</td>
                        <td style="text-align:left;font-style:italic;">${p.extra || '-'}</td>
                    </tr>`;
                }).join('');
            }).join('');
            
            const printWindow = window.open('', '_blank');
            
            const printContent = `
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Pedidos - PANELAIS</title>
                    <style>
                        * { margin: 0; padding: 0; box-sizing: border-box; }
                        body { font-family: Arial, sans-serif; font-size: 9px; padding: 15px; }
                        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #1e293b; }
                        .header-left h1 { font-size: 16px; margin-bottom: 3px; color: #1e293b; }
                        .header-left .date { font-size: 9px; color: #64748b; }
                        .header-right { text-align: right; }
                        .author { font-size: 10px; font-weight: bold; color: #1e293b; }
                        table { width: 100%; border-collapse: collapse; }
                        th { background: #1e293b; color: white; padding: 5px 3px; text-align: center; font-size: 7px; font-weight: bold; text-transform: uppercase; }
                        td { padding: 4px 3px; text-align: center; border-bottom: 1px solid #e2e8f0; font-size: 8px; vertical-align: middle; }
                        tr:nth-child(even) { background: #f8fafc; }
                        .folder-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                        .total { margin-top: 10px; text-align: right; font-weight: bold; font-size: 10px; }
                        @media print { 
                            body { padding: 5px; -webkit-print-color-adjust: exact; print-color-adjust: exact; } 
                            @page { margin: 0.5cm; size: landscape; }
                            th { background: #1e293b !important; color: white !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                            tr.group-child td { border-top: 1px dashed #e2e8f0; }
                        tr.group-first td, tr.group-child td { vertical-align: middle; }
                            .folder-dot { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                        }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <div class="header-left">
                            <h1>PANELAIS - Lista de Pedidos</h1>
                            <span class="date">Generado: ${new Date().toLocaleDateString('es-ES')} ${new Date().toLocaleTimeString('es-ES', {hour: '2-digit', minute:'2-digit'})}</span>
                        </div>
                        <div class="header-right">
                            <span class="author">Elaborado por: David Plaza Yuste</span>
                        </div>
                    </div>
                    
                    <table>
                        <thead>
                            <tr>
                                <th></th>
                                <th>Fecha</th>
                                <th>Oferta</th>
                                <th>N/P</th>
                                <th>Cliente</th>
                                <th>Destino</th>
                                <th></th>
                                <th>Mód.</th>
                                <th>N/S</th>
                                <th>Ud.</th>
                                <th>L</th>
                                <th>A</th>
                                <th>H</th>
                                <th>Estructura</th>
                                <th>Carril/Panel</th>
                                <th>Base</th>
                                <th>Acabado</th>
                                <th>Suministro</th>
                                <th>Perfilado</th>
                                <th>Colores</th>
                                <th>Notas</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rowsHtml}
                        </tbody>
                    </table>
                    
                    <div class="total">Total: ${grupos.length} pedido${grupos.length !== 1 ? 's' : ''} · ${pedidosImprimir.length} módulo${pedidosImprimir.length !== 1 ? 's' : ''}</div>
                    
                    <script>
                        window.onload = function() { window.print(); };
                    <\/script>
                </body>
                </html>
            `;
            
            printWindow.document.write(printContent);
            printWindow.document.close();
        }
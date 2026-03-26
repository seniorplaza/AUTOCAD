// ═══ MODAL ═══════════════════════════════════════════════════════════════════
        const modal = document.getElementById('confirmModal');
        function openModal(title, desc, onConfirm, isOptions = false) {
            document.getElementById('modalTitle').innerText = title;
            document.getElementById('modalDesc').innerText = desc;
            const container = document.getElementById('modalButtons');
            if (isOptions) {
                container.innerHTML = `
                    <button onclick="closeModal()" class="px-4 py-2 text-sm text-slate-400">Cancelar</button>
                    <button id="importMergeBtn" class="px-4 py-2 text-sm bg-blue-600 rounded-lg">Añadir</button>
                    <button id="importReplaceBtn" class="px-4 py-2 text-sm bg-red-600 rounded-lg">Reemplazar</button>
                `;
                document.getElementById('importMergeBtn').onclick = () => { onConfirm('merge'); closeModal(); };
                document.getElementById('importReplaceBtn').onclick = () => { onConfirm('replace'); closeModal(); };
            } else {
                container.innerHTML = `
                    <button onclick="closeModal()" class="px-4 py-2 text-sm text-slate-400">Cancelar</button>
                    <button id="modalConfirmBtn" class="px-4 py-2 text-sm bg-red-600 rounded-lg">Confirmar</button>
                `;
                document.getElementById('modalConfirmBtn').onclick = () => { onConfirm(); closeModal(); };
            }
            modal.style.display = 'flex';
        }
        function closeModal() { modal.style.display = 'none'; }

// ═══ TOP SCROLL SYNC ════════════════════════════════════════════════════════
        // Sync top scrollbar with table container
        (function() {
            function initTopScroll() {
                const top = document.getElementById('topScroll');
                const inner = document.getElementById('topScrollInner');
                const container = document.getElementById('tableContainer');
                if (!top || !inner || !container) return;
                function syncWidth() {
                    inner.style.width = container.scrollWidth + 'px';
                }
                syncWidth();
                new ResizeObserver(syncWidth).observe(container);
                top.addEventListener('scroll', () => { container.scrollLeft = top.scrollLeft; });
                container.addEventListener('scroll', () => { top.scrollLeft = container.scrollLeft; });
                top.addEventListener('wheel', (e) => {
                    if (e.deltaY !== 0 || e.deltaX !== 0) {
                        e.preventDefault();
                        container.scrollLeft += (e.deltaX || e.deltaY) * 2;
                        top.scrollLeft = container.scrollLeft;
                    }
                }, { passive: false });
                // Header: wheel horizontal only on the thead tr (not the tbody)
                const headerEl = document.getElementById('headerRow');
                if (headerEl) {
                    headerEl.addEventListener('wheel', (e) => {
                        if (e.deltaY !== 0 || e.deltaX !== 0) {
                            e.preventDefault();
                            container.scrollLeft += (e.deltaX || e.deltaY) * 2;
                            top.scrollLeft = container.scrollLeft;
                        }
                    }, { passive: false });
                }
            }
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initTopScroll);
            } else {
                initTopScroll();
            }
        })();

// ═══ DELETE / SELECTION ══════════════════════════════════════════════════════
        function askDeleteRow(id) {
            openModal("¿Eliminar?", "Se borrará la fila seleccionada.", () => {
                pushToHistory(); orders = orders.filter(o => o.id !== id); saveList(false); renderTable();
            });
        }

        // Funciones para selección múltiple
        function toggleRowSelection(id) {
            // Encontrar todos los hermanos del mismo pedido (mismo oferta+numPedido+cliente)
            const source = orders.find(o => o.id === id);
            const siblings = source
                ? orders.filter(o =>
                    o.oferta === source.oferta &&
                    o.numPedido === source.numPedido &&
                    o.cliente === source.cliente)
                : [{ id }];

            const adding = !selectedRows.has(id);
            siblings.forEach(s => {
                if (adding) selectedRows.add(s.id);
                else selectedRows.delete(s.id);
            });

            // Actualizar DOM de cada hermano sin re-renderizar
            siblings.forEach(s => {
                const row = document.querySelector(`tr[data-id="${s.id}"]`);
                if (!row) return;
                row.classList.toggle('row-selected', adding);
                const btn = row.querySelector('button[onclick^="toggleRowSelection"]');
                if (btn) {
                    const icon = btn.querySelector('.material-symbols-outlined');
                    if (icon) {
                        icon.textContent = adding ? 'check_circle' : 'radio_button_unchecked';
                        icon.classList.toggle('text-blue-500', adding);
                    }
                    btn.classList.toggle('opacity-0', !adding);
                    btn.classList.toggle('group-hover:opacity-100', !adding);
                }
            });
            updateSelectionUI();
        }

        function toggleSelectAll() {
            // Obtener IDs de filas visibles actualmente
            const visibleRows = document.querySelectorAll('tr[data-id]');
            const visibleIds = Array.from(visibleRows).map(r => parseInt(r.dataset.id));
            
            // Si hay alguna seleccionada, deseleccionar todas; si no, seleccionar todas
            const anySelected = visibleIds.some(id => selectedRows.has(id));
            
            if (anySelected) {
                visibleIds.forEach(id => selectedRows.delete(id));
            } else {
                visibleIds.forEach(id => selectedRows.add(id));
            }
            renderTable();
        }

        function updateSelectionUI() {
            const count = selectedRows.size;
            const badge = document.getElementById('selectedBadge');
            const printBadge = document.getElementById('printBadge');
            
            // Actualizar badge en el botón de borrar (solo mostrar si hay 2 o más)
            if (badge) {
                if (count >= 2) {
                    badge.classList.remove('hidden');
                    badge.classList.add('flex');
                    badge.textContent = count;
                } else {
                    badge.classList.add('hidden');
                    badge.classList.remove('flex');
                }
            }
            
            // Actualizar badge en el botón de imprimir (solo mostrar si hay 2 o más)
            if (printBadge) {
                if (count >= 2) {
                    printBadge.classList.remove('hidden');
                    printBadge.classList.add('flex');
                    printBadge.textContent = count;
                } else {
                    printBadge.classList.add('hidden');
                    printBadge.classList.remove('flex');
                }
            }
        }

        function askDeleteSelected() {
            const count = selectedRows.size;
            if (count === 0) return;
            
            openModal(`¿Eliminar ${count} fila${count > 1 ? 's' : ''}?`, `Se borrarán las ${count} fila${count > 1 ? 's' : ''} seleccionada${count > 1 ? 's' : ''}.`, () => {
                pushToHistory();
                orders = orders.filter(o => !selectedRows.has(o.id));
                selectedRows.clear();
                saveList(false);
                renderTable();
            });
        }

// ═══ CLEAR / FILE IMPORT ════════════════════════════════════════════════════
        function askClearOrSelected() {
            const count = selectedRows.size;
            if (count > 0) {
                // Si hay filas seleccionadas, borrar solo esas
                openModal(`¿Eliminar ${count} fila${count > 1 ? 's' : ''}?`, `Se borrarán las ${count} fila${count > 1 ? 's' : ''} seleccionada${count > 1 ? 's' : ''}.`, () => {
                    pushToHistory();
                    orders = orders.filter(o => !selectedRows.has(o.id));
                    selectedRows.clear();
                    saveList(false);
                    renderTable();
                });
            } else {
                // Si no hay selección, borrar todo
                openModal("¿BORRAR TODO?", "Limpiarás la tabla completa.", () => {
                    pushToHistory();
                    orders = [];
                    saveList(false);
                    renderTable();
                });
            }
        }

        function askClearAll() {
            openModal("¿BORRAR TODO?", "Limpiarás la tabla completa.", () => {
                pushToHistory(); orders = []; saveList(false); renderTable();
            });
        }

        function handleFileUpload(event) {
            const file = event.target.files[0]; if (!file) return;
            const reader = new FileReader(); reader.onload = e => processCSV(e.target.result);
            reader.readAsText(file); event.target.value = '';
        }

// ═══ FILTER FUNCTIONS ════════════════════════════════════════════════════════
        function handleFilter(e) {
            const colId = e.target.dataset.col; filters[colId] = e.target.value;
            document.getElementById(`clear-${colId}`).classList.toggle('visible', !!e.target.value); debouncedRenderTable();
        }

        function clearSingleFilter(colId) {
            const input = document.querySelector(`.filter-input[data-col="${colId}"]`);
            if (input) { input.value = ''; filters[colId] = ''; document.getElementById(`clear-${colId}`).classList.remove('visible'); renderTable(); }
        }

        function toggleFilterRow() { document.querySelectorAll('.filter-row').forEach(row => row.classList.toggle('show')); }
        function clearFilters() {
            document.querySelectorAll('.filter-input').forEach(i => i.value = '');
            document.querySelectorAll('.clear-filter-btn').forEach(b => b.classList.remove('visible'));
            filters = { favorite: false, folder: null, fechaDesde: null, fechaHasta: null }; 
            renderHeaders();
            renderTable();
        }

        function updateFilterStatus() {
            const active = Object.keys(filters).some(key => {
                if (key === 'favorite') return filters[key] === true;
                if (key === 'folder') return filters[key] !== null;
                return filters[key] && filters[key] !== '';
            });
            document.getElementById('filterBadge').classList.toggle('hidden', !active);
            document.getElementById('clearFiltersBtn').classList.toggle('hidden', !active);
        }

// ═══ THEME / FULLSCREEN ══════════════════════════════════════════════════════
        function toggleTheme() {
            // Modo oscuro permanente - sin cambio de tema
            document.documentElement.classList.add('dark');
        }

        function loadTheme() {
            // Siempre cargar en modo oscuro
            document.documentElement.classList.add('dark');
        }

        function toggleFullscreen() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(err => {
                    console.log('Error al activar pantalla completa:', err);
                });
            } else {
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                }
            }
        }

// ═══ DATEPICKER ═════════════════════════════════════════════════════════════
        // ============ DATEPICKER ============
        let datepickerState = {
            isOpen: false,
            currentId: null,
            currentDate: new Date(),
            selectedDate: null,
            isRevisionDate: false
        };

        const mesesES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
        const diasSemanaES = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sá', 'Do'];

        function openDatepicker(event, id, isRevisionDate = false) {
            event.stopPropagation();
            const cell = event.currentTarget;
            const rect = cell.getBoundingClientRect();
            
            // Parsear fecha actual del registro
            const order = orders.find(o => o.id === id);
            let fechaActual = '';
            
            // Si es fecha de revisión en modo ofertas, obtener la fecha de la revisión actual
            if (isRevisionDate && modoActual === 'ofertas') {
                fechaActual = getFechaRev(order);
            } else {
                fechaActual = order?.fecha || '';
            }
            
            if (fechaActual && fechaActual !== '-') {
                const parts = fechaActual.split('/');
                if (parts.length === 3) {
                    datepickerState.currentDate = new Date(parseInt(parts[2]), parseInt(parts[1]) - 1, parseInt(parts[0]));
                    datepickerState.selectedDate = new Date(parseInt(parts[2]), parseInt(parts[1]) - 1, parseInt(parts[0]));
                }
            } else {
                datepickerState.currentDate = new Date();
                datepickerState.selectedDate = null;
            }
            
            datepickerState.currentId = id;
            datepickerState.isRevisionDate = isRevisionDate;
            datepickerState.isOpen = true;
            
            renderDatepicker(rect);
        }

        function renderDatepicker(rect) {
            const container = document.getElementById('datepickerContainer');
            const year = datepickerState.currentDate.getFullYear();
            const month = datepickerState.currentDate.getMonth();
            
            // Calcular posición
            let top = rect.bottom + 8;
            let left = rect.left;
            
            // Ajustar si se sale de la pantalla
            if (left + 300 > window.innerWidth) {
                left = window.innerWidth - 310;
            }
            if (top + 350 > window.innerHeight) {
                top = rect.top - 358;
            }
            
            container.innerHTML = `
                <div class="datepicker-overlay" onclick="closeDatepicker()"></div>
                <div class="datepicker" style="top: ${top}px; left: ${left}px;">
                    <div class="datepicker-header">
                        <button onclick="event.stopPropagation(); changeMonth(-1)">
                            <span class="material-symbols-outlined">chevron_left</span>
                        </button>
                        <span class="datepicker-title">${mesesES[month]} ${year}</span>
                        <button onclick="event.stopPropagation(); changeMonth(1)">
                            <span class="material-symbols-outlined">chevron_right</span>
                        </button>
                    </div>
                    <div class="datepicker-weekdays">
                        ${diasSemanaES.map(d => `<div class="datepicker-weekday">${d}</div>`).join('')}
                    </div>
                    <div class="datepicker-days">
                        ${generateDays(year, month)}
                    </div>
                    <div class="datepicker-footer">
                        <button class="datepicker-clear-btn" onclick="event.stopPropagation(); clearDate()">Borrar</button>
                        <button class="datepicker-today-btn" onclick="event.stopPropagation(); selectToday()">Hoy</button>
                    </div>
                </div>
            `;
        }

        function generateDays(year, month) {
            const firstDay = new Date(year, month, 1);
            const lastDay = new Date(year, month + 1, 0);
            const startDay = (firstDay.getDay() + 6) % 7; // Lunes = 0
            const daysInMonth = lastDay.getDate();
            
            const today = new Date();
            const todayStr = `${today.getDate()}/${today.getMonth()}/${today.getFullYear()}`;
            
            let days = '';
            
            // Días del mes anterior
            const prevMonth = new Date(year, month, 0);
            const prevDays = prevMonth.getDate();
            for (let i = startDay - 1; i >= 0; i--) {
                const day = prevDays - i;
                days += `<button class="datepicker-day other-month" onclick="event.stopPropagation(); selectDate(${year}, ${month - 1}, ${day})">${day}</button>`;
            }
            
            // Días del mes actual
            for (let day = 1; day <= daysInMonth; day++) {
                const dateStr = `${day}/${month}/${year}`;
                const isToday = dateStr === todayStr;
                const isSelected = datepickerState.selectedDate && 
                    datepickerState.selectedDate.getDate() === day && 
                    datepickerState.selectedDate.getMonth() === month && 
                    datepickerState.selectedDate.getFullYear() === year;
                
                let classes = 'datepicker-day';
                if (isToday) classes += ' today';
                if (isSelected) classes += ' selected';
                
                days += `<button class="${classes}" onclick="event.stopPropagation(); selectDate(${year}, ${month}, ${day})">${day}</button>`;
            }
            
            // Días del mes siguiente
            const totalCells = Math.ceil((startDay + daysInMonth) / 7) * 7;
            const nextDays = totalCells - startDay - daysInMonth;
            for (let day = 1; day <= nextDays; day++) {
                days += `<button class="datepicker-day other-month" onclick="event.stopPropagation(); selectDate(${year}, ${month + 1}, ${day})">${day}</button>`;
            }
            
            return days;
        }

        function changeMonth(delta) {
            datepickerState.currentDate.setMonth(datepickerState.currentDate.getMonth() + delta);
            const rect = document.querySelector('.datepicker').getBoundingClientRect();
            renderDatepicker({ bottom: rect.top - 8, left: rect.left, top: rect.bottom + 8 });
        }

        function selectDate(year, month, day) {
            const date = new Date(year, month, day);
            const formattedDate = `${String(day).padStart(2, '0')}/${String(month + 1).padStart(2, '0')}/${year}`;
            
            // Si es fecha de revisión, actualizar fechasRev
            if (datepickerState.isRevisionDate && modoActual === 'ofertas') {
                const index = orders.findIndex(o => o.id === datepickerState.currentId);
                if (index !== -1) {
                    const rev = orders[index].revision || 0;
                    if (rev > 0) {
                        pushToHistory();
                        if (!orders[index].fechasRev) orders[index].fechasRev = {};
                        orders[index].fechasRev[rev] = formattedDate;
                        saveList(false);
                    }
                }
            } else {
                // Actualizar fecha normal
                updateValue(datepickerState.currentId, 'fecha', formattedDate);
            }
            
            closeDatepicker();
            
            // Actualizar solo la celda de fecha sin re-renderizar toda la tabla
            const row = document.querySelector(`tr[data-id="${datepickerState.currentId}"]`);
            if (row) {
                const fechaCell = row.querySelector('td:first-child');
                if (fechaCell) {
                    fechaCell.textContent = formattedDate;
                }
            }
        }

        function selectToday() {
            const today = new Date();
            selectDate(today.getFullYear(), today.getMonth(), today.getDate());
        }

        function clearDate() {
            // Si es fecha de revisión, limpiar fechasRev
            if (datepickerState.isRevisionDate && modoActual === 'ofertas') {
                const index = orders.findIndex(o => o.id === datepickerState.currentId);
                if (index !== -1) {
                    const rev = orders[index].revision || 0;
                    if (rev > 0) {
                        pushToHistory();
                        if (orders[index].fechasRev && orders[index].fechasRev[rev]) {
                            delete orders[index].fechasRev[rev];
                        }
                        saveList(false);
                    }
                }
            } else {
                // Limpiar fecha normal
                updateValue(datepickerState.currentId, 'fecha', '-');
            }
            
            closeDatepicker();
            
            // Actualizar solo la celda de fecha sin re-renderizar toda la tabla
            const row = document.querySelector(`tr[data-id="${datepickerState.currentId}"]`);
            if (row) {
                const fechaCell = row.querySelector('td:first-child');
                if (fechaCell) {
                    fechaCell.textContent = '-';
                }
            }
        }

        function closeDatepicker() {
            datepickerState.isOpen = false;
            document.getElementById('datepickerContainer').innerHTML = '';
        }


// ═══ DATE RANGE PICKER ══════════════════════════════════════════════════════
        // ============ DATE RANGE PICKER (FILTRO) ============
        let dateRangeState = {
            isOpen: false,
            selectingField: null, // 'desde' o 'hasta'
            tempDesde: null,
            tempHasta: null,
            currentDate: new Date()
        };

        function getDateRangeLabel() {
            if (filters.fechaDesde && filters.fechaHasta) {
                return `${formatShortDate(filters.fechaDesde)} - ${formatShortDate(filters.fechaHasta)}`;
            } else if (filters.fechaDesde) {
                return `Desde ${formatShortDate(filters.fechaDesde)}`;
            } else if (filters.fechaHasta) {
                return `Hasta ${formatShortDate(filters.fechaHasta)}`;
            }
            return 'Rango';
        }

        function formatShortDate(dateStr) {
            if (!dateStr) return '';
            const parts = dateStr.split('/');
            if (parts.length === 3) {
                return `${parts[0]}/${parts[1]}`;
            }
            return dateStr;
        }

        function openDateRangePicker(event) {
            event.stopPropagation();
            const btn = event.currentTarget;
            const rect = btn.getBoundingClientRect();
            
            dateRangeState.isOpen = true;
            dateRangeState.tempDesde = filters.fechaDesde;
            dateRangeState.tempHasta = filters.fechaHasta;
            dateRangeState.selectingField = null;
            dateRangeState.currentDate = new Date();
            
            renderDateRangePicker(rect);
        }

        function renderDateRangePicker(rect) {
            const container = document.getElementById('datepickerContainer');
            
            let top = rect.bottom + 8;
            let left = rect.left;
            
            if (left + 340 > window.innerWidth) {
                left = window.innerWidth - 350;
            }
            if (top + 450 > window.innerHeight) {
                top = rect.top - 458;
            }
            
            const year = dateRangeState.currentDate.getFullYear();
            const month = dateRangeState.currentDate.getMonth();
            
            container.innerHTML = `
                <div class="datepicker-overlay" onclick="closeDateRangePicker()"></div>
                <div class="date-range-picker" style="top: ${top}px; left: ${left}px;">
                    <div class="date-range-header">
                        <span class="date-range-title">Filtrar por rango de fechas</span>
                    </div>
                    
                    <div class="date-range-inputs">
                        <div class="date-range-field">
                            <label class="date-range-label">Desde</label>
                            <input type="text" class="date-range-input ${dateRangeState.selectingField === 'desde' ? 'ring-2 ring-blue-500' : ''}" 
                                id="rangeDesdeInput"
                                value="${dateRangeState.tempDesde || ''}" 
                                placeholder="dd/mm/aaaa"
                                onclick="event.stopPropagation(); setSelectingField('desde')"
                                readonly>
                        </div>
                        <div class="date-range-field">
                            <label class="date-range-label">Hasta</label>
                            <input type="text" class="date-range-input ${dateRangeState.selectingField === 'hasta' ? 'ring-2 ring-blue-500' : ''}" 
                                id="rangeHastaInput"
                                value="${dateRangeState.tempHasta || ''}" 
                                placeholder="dd/mm/aaaa"
                                onclick="event.stopPropagation(); setSelectingField('hasta')"
                                readonly>
                        </div>
                    </div>
                    
                    <div class="date-range-presets">
                        <button class="date-range-preset" onclick="event.stopPropagation(); applyPreset('hoy')">Hoy</button>
                        <button class="date-range-preset" onclick="event.stopPropagation(); applyPreset('semana')">Esta semana</button>
                        <button class="date-range-preset" onclick="event.stopPropagation(); applyPreset('mes')">Este mes</button>
                        <button class="date-range-preset" onclick="event.stopPropagation(); applyPreset('trimestre')">Últimos 3 meses</button>
                        <button class="date-range-preset" onclick="event.stopPropagation(); applyPreset('año')">Este año</button>
                    </div>
                    
                    <div class="datepicker-header">
                        <button onclick="event.stopPropagation(); changeRangeMonth(-1)">
                            <span class="material-symbols-outlined">chevron_left</span>
                        </button>
                        <span class="datepicker-title">${mesesES[month]} ${year}</span>
                        <button onclick="event.stopPropagation(); changeRangeMonth(1)">
                            <span class="material-symbols-outlined">chevron_right</span>
                        </button>
                    </div>
                    <div class="datepicker-weekdays">
                        ${diasSemanaES.map(d => `<div class="datepicker-weekday">${d}</div>`).join('')}
                    </div>
                    <div class="datepicker-days">
                        ${generateRangeDays(year, month)}
                    </div>
                    
                    <div class="date-range-actions">
                        <button class="date-range-btn date-range-btn-clear" onclick="event.stopPropagation(); clearDateRange()">Limpiar</button>
                        <button class="date-range-btn date-range-btn-cancel" onclick="event.stopPropagation(); closeDateRangePicker()">Cancelar</button>
                        <button class="date-range-btn date-range-btn-apply" onclick="event.stopPropagation(); applyDateRange()">Aplicar</button>
                    </div>
                </div>
            `;
        }

        function generateRangeDays(year, month) {
            const firstDay = new Date(year, month, 1);
            const lastDay = new Date(year, month + 1, 0);
            const startDay = (firstDay.getDay() + 6) % 7;
            const daysInMonth = lastDay.getDate();
            
            const today = new Date();
            const todayStr = `${today.getDate()}/${today.getMonth()}/${today.getFullYear()}`;
            
            let days = '';
            
            // Días del mes anterior
            const prevMonth = new Date(year, month, 0);
            const prevDays = prevMonth.getDate();
            for (let i = startDay - 1; i >= 0; i--) {
                const day = prevDays - i;
                days += `<button class="datepicker-day other-month" onclick="event.stopPropagation(); selectRangeDate(${year}, ${month - 1}, ${day})">${day}</button>`;
            }
            
            // Días del mes actual
            for (let day = 1; day <= daysInMonth; day++) {
                const dateStr = `${String(day).padStart(2, '0')}/${String(month + 1).padStart(2, '0')}/${year}`;
                const isToday = `${day}/${month}/${year}` === todayStr;
                const isDesde = dateRangeState.tempDesde === dateStr;
                const isHasta = dateRangeState.tempHasta === dateStr;
                const isInRange = isDateInRange(dateStr);
                
                let classes = 'datepicker-day';
                if (isToday) classes += ' today';
                if (isDesde || isHasta) classes += ' selected';
                if (isInRange && !isDesde && !isHasta) classes += ' bg-blue-500/20';
                
                days += `<button class="${classes}" onclick="event.stopPropagation(); selectRangeDate(${year}, ${month}, ${day})">${day}</button>`;
            }
            
            // Días del mes siguiente
            const totalCells = Math.ceil((startDay + daysInMonth) / 7) * 7;
            const nextDays = totalCells - startDay - daysInMonth;
            for (let day = 1; day <= nextDays; day++) {
                days += `<button class="datepicker-day other-month" onclick="event.stopPropagation(); selectRangeDate(${year}, ${month + 1}, ${day})">${day}</button>`;
            }
            
            return days;
        }

        function isDateInRange(dateStr) {
            if (!dateRangeState.tempDesde || !dateRangeState.tempHasta) return false;
            const date = parseDate(dateStr);
            const desde = parseDate(dateRangeState.tempDesde);
            const hasta = parseDate(dateRangeState.tempHasta);
            return date > desde && date < hasta;
        }

        function setSelectingField(field) {
            dateRangeState.selectingField = field;
            const btn = document.getElementById('dateRangeBtn');
            if (btn) {
                renderDateRangePicker(btn.getBoundingClientRect());
            }
        }

        function selectRangeDate(year, month, day) {
            const formattedDate = `${String(day).padStart(2, '0')}/${String(month + 1).padStart(2, '0')}/${year}`;
            
            if (dateRangeState.selectingField === 'desde') {
                dateRangeState.tempDesde = formattedDate;
                dateRangeState.selectingField = 'hasta';
            } else if (dateRangeState.selectingField === 'hasta') {
                dateRangeState.tempHasta = formattedDate;
                dateRangeState.selectingField = null;
            } else {
                // Si no hay campo seleccionado, empezar con desde
                dateRangeState.tempDesde = formattedDate;
                dateRangeState.selectingField = 'hasta';
            }
            
            // Validar que desde <= hasta
            if (dateRangeState.tempDesde && dateRangeState.tempHasta) {
                const desde = parseDate(dateRangeState.tempDesde);
                const hasta = parseDate(dateRangeState.tempHasta);
                if (desde > hasta) {
                    // Intercambiar
                    const temp = dateRangeState.tempDesde;
                    dateRangeState.tempDesde = dateRangeState.tempHasta;
                    dateRangeState.tempHasta = temp;
                }
            }
            
            dateRangeState.currentDate = new Date(year, month, 1);
            const btn = document.getElementById('dateRangeBtn');
            if (btn) {
                renderDateRangePicker(btn.getBoundingClientRect());
            }
        }

        function changeRangeMonth(delta) {
            dateRangeState.currentDate.setMonth(dateRangeState.currentDate.getMonth() + delta);
            const btn = document.getElementById('dateRangeBtn');
            if (btn) {
                renderDateRangePicker(btn.getBoundingClientRect());
            }
        }

        function applyPreset(preset) {
            const today = new Date();
            let desde, hasta;
            
            switch(preset) {
                case 'hoy':
                    desde = hasta = formatDateForFilter(today);
                    break;
                case 'semana':
                    const startOfWeek = new Date(today);
                    startOfWeek.setDate(today.getDate() - today.getDay() + 1);
                    desde = formatDateForFilter(startOfWeek);
                    hasta = formatDateForFilter(today);
                    break;
                case 'mes':
                    desde = formatDateForFilter(new Date(today.getFullYear(), today.getMonth(), 1));
                    hasta = formatDateForFilter(today);
                    break;
                case 'trimestre':
                    desde = formatDateForFilter(new Date(today.getFullYear(), today.getMonth() - 3, today.getDate()));
                    hasta = formatDateForFilter(today);
                    break;
                case 'año':
                    desde = formatDateForFilter(new Date(today.getFullYear(), 0, 1));
                    hasta = formatDateForFilter(today);
                    break;
            }
            
            dateRangeState.tempDesde = desde;
            dateRangeState.tempHasta = hasta;
            
            const btn = document.getElementById('dateRangeBtn');
            if (btn) {
                renderDateRangePicker(btn.getBoundingClientRect());
            }
        }

        function formatDateForFilter(date) {
            return `${String(date.getDate()).padStart(2, '0')}/${String(date.getMonth() + 1).padStart(2, '0')}/${date.getFullYear()}`;
        }

        function applyDateRange() {
            filters.fechaDesde = dateRangeState.tempDesde;
            filters.fechaHasta = dateRangeState.tempHasta;
            closeDateRangePicker();
            renderHeaders();
            renderTable();
        }

        function clearDateRange() {
            dateRangeState.tempDesde = null;
            dateRangeState.tempHasta = null;
            filters.fechaDesde = null;
            filters.fechaHasta = null;
            closeDateRangePicker();
            renderHeaders();
            renderTable();
        }

        function closeDateRangePicker() {
            dateRangeState.isOpen = false;
            document.getElementById('datepickerContainer').innerHTML = '';
        }

        window.onload = function() {
            loadTheme();
            loadData();
        };
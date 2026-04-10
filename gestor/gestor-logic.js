// ═══ STATE VARIABLES ══════════════════════════════════════════════════════════
        let orders = [];
        let history = [];
        let filters = { favorite: false, folder: null, fechaDesde: null, fechaHasta: null };
        let currentSort = { key: 'fecha', direction: 'desc' };
        let modoActual = 'pedidos'; // 'pedidos' o 'ofertas'
        let selectedRows = new Set(); // Filas seleccionadas para eliminación múltiple

        // Memoization cache para calcularCorreas (opt. 3)
        let _correasCache = new Map();

// Debounce helper
        // Debounce helper (opt. 4)
        function debounce(fn, delay) {
            let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
        }
        const debouncedRenderTable = debounce(() => renderTable(), 200);

// ═══ PERFILADO ═══════════════════════════════════════════════════════════════
        // Función para toggle del menú de perfilado
        function togglePerfiladoMenu(event, id) {
            event.stopPropagation();
            const menuId = `perfilado-menu-${id}`;
            const menu = document.getElementById(menuId);
            
            // Cerrar todos los otros menús
            document.querySelectorAll('.perfilado-menu').forEach(m => {
                if (m.id !== menuId) m.classList.remove('show');
            });
            
            // Toggle del menú actual
            menu.classList.toggle('show');
        }

        // Función para establecer el perfilado seleccionado
        function setPerfilado(id, value) {
            const index = orders.findIndex(o => o.id === id);
            if (index !== -1) {
                pushToHistory();
                orders[index].perfilado = value;
                saveList(false);
                renderTable();
            }
            // Cerrar menús
            document.querySelectorAll('.perfilado-menu').forEach(m => m.classList.remove('show'));
        }

// ═══ COLOR FUNCTIONS ═══════════════════════════════════════════════════════════
        // Función para determinar si usar texto blanco o negro según el color de fondo
        function getContrastColor(hexColor) {
            if (!hexColor || hexColor === '') return '#0f172a';
            const r = parseInt(hexColor.substr(1, 2), 16);
            const g = parseInt(hexColor.substr(3, 2), 16);
            const b = parseInt(hexColor.substr(5, 2), 16);
            const yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;
            return (yiq >= 128) ? '#0f172a' : '#ffffff';
        }

        // Toggle del menú de colores RAL
        function toggleColorMenu(event, id, type) {
            event.stopPropagation();
            const menuId = `color-menu-${id}-${type}`;
            const menu = document.getElementById(menuId);
            
            // Cerrar todos los otros menús
            document.querySelectorAll('.color-menu').forEach(m => {
                if (m.id !== menuId) m.classList.remove('show');
            });
            
            // Toggle del menú actual
            if (!menu.classList.contains('show')) {
                // Generar opciones si el menú está vacío
                if (menu.innerHTML === '') {
                    menu.innerHTML = ralColors.map(color => `
                        <div class="color-option" onclick="setColor(${id}, '${type}', '${color.code}')">
                            <div class="color-option-swatch" style="background-color: ${color.code}"></div>
                            <span style="color: #e2e8f0">${color.name}</span>
                        </div>
                    `).join('');
                }
                menu.classList.add('show');
            } else {
                menu.classList.remove('show');
            }
        }

        // Establecer color seleccionado
        function setColor(id, type, color) {
            const index = orders.findIndex(o => o.id === id);
            if (index !== -1) {
                pushToHistory();
                const fieldMap = { 'panel': 'colorPanel', 'estructura': 'colorEstructura', 'carpinteria': 'colorCarpinteria' };
                orders[index][fieldMap[type]] = color;
                saveList(false);
                renderTable();
            }
            // Cerrar menú
            document.querySelectorAll('.color-menu').forEach(m => m.classList.remove('show'));
        }

// ═══ DATA LOAD ═══════════════════════════════════════════════════════════════
        function loadData() {
            const saved = localStorage.getItem('fabricacion_orders');
            orders = saved ? JSON.parse(saved) : [...INITIAL_DB];
            
            // Migrar datos antiguos: convertir boolean a números y panel a panelGrosor/panelTipo
            orders = orders.map(order => {
                const migrated = {
                    ...order,
                    printed: typeof order.printed === 'boolean' ? (order.printed ? 2 : 0) : (order.printed || 0),
                    sent: typeof order.sent === 'boolean' ? (order.sent ? 2 : 0) : (order.sent || 0),
                    delivered: typeof order.delivered === 'number' ? (order.delivered > 0) : (order.delivered || false)
                };
                
                // Migrar panel antiguo a panelGrosor y panelTipo
                if (order.panel && !order.panelGrosor && !order.panelTipo) {
                    const panelValue = order.panel.toString();
                    // Si es número, asumimos que es grosor
                    if (['30', '40', '50', '60', '80', '100'].includes(panelValue)) {
                        migrated.panelGrosor = panelValue;
                        migrated.panelTipo = '';
                    }
                    // Si es PUR, PIR o LDR, asumimos que es tipo
                    else if (['PUR', 'PIR', 'LDR'].includes(panelValue)) {
                        migrated.panelGrosor = '';
                        migrated.panelTipo = panelValue;
                    }
                    delete migrated.panel;
                }
                
                // Asegurar que existen los campos
                if (!migrated.panelGrosor) migrated.panelGrosor = '';
                if (!migrated.panelTipo) migrated.panelTipo = '';
                if (!migrated.cubierta) migrated.cubierta = 'ESTÁNDAR';
                if (!migrated.estBase) migrated.estBase = '';
                if (!migrated.estCubierta) migrated.estCubierta = '';
                if (!migrated.estPilar) migrated.estPilar = '';
                if (!migrated.folderPath) migrated.folderPath = '';
                if (migrated.tipoRegistro === undefined) migrated.tipoRegistro = 0;
                if (migrated.revision === undefined) migrated.revision = 0;
                if (!migrated.revHecha) migrated.revHecha = {};
                if (!migrated.notasRev) migrated.notasRev = {};
                if (!migrated.fechasRev) migrated.fechasRev = {};
                if (migrated.numPedido === undefined) migrated.numPedido = '';
                if (!migrated.modulo) migrated.modulo = 'M1';
                if (!migrated.cantidad) migrated.cantidad = 1;
                if (migrated.conjunto === undefined) migrated.conjunto = false;
                if (migrated.conjuntoVinculado === undefined) migrated.conjuntoVinculado = false;
                if (migrated.adosamiento === undefined) migrated.adosamiento = null;

                return migrated;
            });

            // Migración: separar filas que tienen "/" en L o A en filas individuales
            const expanded = [];
            orders.forEach(order => {
                const lParts = (order.l || '').toString().split('/').map(s => s.trim()).filter(Boolean);
                const aParts = (order.a || '').toString().split('/').map(s => s.trim()).filter(Boolean);
                const hParts = (order.h || '').toString().split('/').map(s => s.trim()).filter(Boolean);
                const count = Math.max(lParts.length, aParts.length, 1);

                if (count > 1) {
                    for (let i = 0; i < count; i++) {
                        expanded.push({
                            ...order,
                            id: i === 0 ? order.id : Date.now() + Math.random(),
                            l: lParts[i] || lParts[lParts.length - 1] || order.l,
                            a: aParts[i] || aParts[aParts.length - 1] || order.a,
                            h: hParts[i] || hParts[hParts.length - 1] || order.h,
                            modulo: `M${i + 1}`
                        });
                    }
                } else {
                    expanded.push(order);
                }
            });
            orders = expanded;
            
            renderHeaders();
            renderTable();
            initCellNavigation();
        }

// ═══ CSV EXPORT/IMPORT ═══════════════════════════════════════════════════════
        function exportToCSV() {
            let csv = "\uFEFFFecha;Oferta;NumPedido;Cliente;Destino;Serie;L;A;H;EstBase;EstCubierta;EstPilar;Cubierta;PanelGrosor;PanelTipo;Base;Acabado;Suministro;Perfilado;ColorPanel;ColorEstructura;ColorCarpinteria;Notas;FolderPath;Impreso;Enviado;Entregado;TipoRegistro;Revision;RevHecha;NotasRev;FechasRev;Favorito;Carpeta;Modulo;Cantidad;Conjunto;Adosamiento\n";
            orders.forEach(i => {
                const folderVal = i.folder || "";
                const favVal = i.favorite ? "true" : "false";
                const printedVal = i.printed || 0;
                const sentVal = i.sent || 0;
                const deliveredVal = i.delivered ? "true" : "false";
                const tipoRegistroVal = i.tipoRegistro || 0;
                const revisionVal = i.revision || 0;
                const revHechaVal = JSON.stringify(i.revHecha || {});
                const notasRevVal = JSON.stringify(i.notasRev || {});
                const fechasRevVal = JSON.stringify(i.fechasRev || {});
                const panelGrosor = i.panelGrosor || "";
                const panelTipo = i.panelTipo || "";
                const estBase = i.estBase || "";
                const estCubierta = i.estCubierta || "";
                const estPilar = i.estPilar || "";
                const folderPath = i.folderPath || "";
                const numPedido = i.numPedido || "";
                const adosamientoVal = i.adosamiento ? JSON.stringify(i.adosamiento) : "";
                csv += `${i.fecha};${i.oferta};${numPedido};${i.cliente};${i.destino};${i.serie};${i.l};${i.a};${i.h};${estBase};${estCubierta};${estPilar};${i.cubierta || ""};${panelGrosor};${panelTipo};${i.base || ""};${i.acabado || ""};${i.suministro || ""};${i.perfilado || ""};${i.colorPanel || ""};${i.colorEstructura || ""};${i.colorCarpinteria || ""};${i.extra};${folderPath};${printedVal};${sentVal};${deliveredVal};${tipoRegistroVal};${revisionVal};${revHechaVal};${notasRevVal};${fechasRevVal};${favVal};${folderVal};${i.modulo || "M1"};${i.cantidad || 1};${i.conjunto ? "true" : "false"};${adosamientoVal};${i.conjuntoVinculado ? "true" : "false"}\n`;
            });
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = `pedidos_fabricacion_${new Date().toLocaleDateString().replace(/\//g, '-')}.csv`;
            a.click();
        }

        function processCSV(text) {
            const lines = text.split(/\r?\n/).filter(l => l.trim() !== "");
            if (lines.length < 2) return;
            
            const imported = lines.slice(1).map((line, i) => {
                const v = line.split(/[;]/); 
                const parts = v.length > 1 ? v : line.split(/[,]/);

                // Intentar parsear revHecha como JSON
                let revHechaParsed = {};
                try {
                    if (parts[29]) revHechaParsed = JSON.parse(parts[29]);
                } catch(e) { revHechaParsed = {}; }

                // Intentar parsear notasRev como JSON
                let notasRevParsed = {};
                try {
                    if (parts[30]) notasRevParsed = JSON.parse(parts[30]);
                } catch(e) { notasRevParsed = {}; }

                // Intentar parsear fechasRev como JSON
                let fechasRevParsed = {};
                try {
                    if (parts[31]) fechasRevParsed = JSON.parse(parts[31]);
                } catch(e) { fechasRevParsed = {}; }

                return {
                    id: Date.now() + i,
                    fecha: parts[0] || "",
                    oferta: parts[1] || "",
                    numPedido: parts[2] || "",
                    cliente: parts[3] || "",
                    destino: parts[4] || "",
                    serie: parts[5] || "",
                    l: parts[6] || "0",
                    a: parts[7] || "0",
                    h: parts[8] || "0",
                    estBase: parts[9] || "",
                    estCubierta: parts[10] || "",
                    estPilar: parts[11] || "",
                    cubierta: parts[12] || "",
                    panelGrosor: parts[13] || "",
                    panelTipo: parts[14] || "",
                    base: parts[15] || "",
                    acabado: parts[16] || "",
                    suministro: parts[17] || "",
                    perfilado: parts[18] || "",
                    colorPanel: parts[19] || "",
                    colorEstructura: parts[20] || "",
                    colorCarpinteria: parts[21] || "",
                    extra: parts[22] || "",
                    folderPath: parts[23] || "",
                    printed: parts[24] === "true" ? 2 : (isNaN(parseInt(parts[24])) ? 0 : parseInt(parts[24])),
                    sent: parts[25] === "true" ? 2 : (isNaN(parseInt(parts[25])) ? 0 : parseInt(parts[25])),
                    delivered: (parts[26] === "true"),
                    tipoRegistro: isNaN(parseInt(parts[27])) ? 0 : parseInt(parts[27]),
                    revision: isNaN(parseInt(parts[28])) ? 0 : parseInt(parts[28]),
                    revHecha: revHechaParsed,
                    notasRev: notasRevParsed,
                    fechasRev: fechasRevParsed,
                    favorite: (parts[32] === "true"),
                    folder: (parts[33] && parts[33].trim() !== "") ? parts[33].trim() : null,
                    modulo:   (parts[34] && parts[34].trim()) ? parts[34].trim() : 'M1',
                    cantidad: isNaN(parseInt(parts[35])) ? 1 : parseInt(parts[35]),
                    conjunto: (parts[36] === 'true'),
                    adosamiento: (() => { try { return parts[37] && parts[37].trim() ? JSON.parse(parts[37]) : null; } catch(e) { return null; } })(),
                    conjuntoVinculado: (parts[38] === 'true')
                };
            });

            openModal("Importar", `¿Añadir o reemplazar datos actuales?`, mode => {
                pushToHistory();
                orders = mode === 'replace' ? imported : [...imported, ...orders];
                saveList(false);
                renderTable();
            }, true);
        }

// ═══ FILTER/SORT ═════════════════════════════════════════════════════════════
        function toggleFavFilter() { filters.favorite = !filters.favorite; renderTable(); }
        function toggleColorFilter(color) { filters.folder = (filters.folder === color) ? null : color; renderTable(); }
        function updateActionFiltersUI() {
            const favBtn = document.getElementById('favFilterBtn');
            if (favBtn) {
                const icon = favBtn.querySelector('.material-symbols-outlined');
                if (filters.favorite) { favBtn.classList.add('active'); icon.style.fontVariationSettings = "'FILL' 1"; } 
                else { favBtn.classList.remove('active'); icon.style.fontVariationSettings = "'FILL' 0"; }
            }
            document.querySelectorAll('.color-filter-dot').forEach(dot => dot.classList.toggle('active', dot.dataset.color === filters.folder));
        }

        function toggleSortMenu(e, colId) {
            e.stopPropagation();
            const allMenus = document.querySelectorAll('.sort-menu');
            const targetMenu = document.getElementById(`sort-menu-${colId}`);
            const isVisible = targetMenu.style.display === 'block';
            allMenus.forEach(m => m.style.display = 'none');
            if (!isVisible) targetMenu.style.display = 'block';
        }

        function closeAllMenus(e) {
            document.querySelectorAll('.sort-menu').forEach(m => m.style.display = 'none');
            document.querySelectorAll('.folder-menu').forEach(m => m.classList.remove('show'));
            document.querySelectorAll('.color-menu').forEach(m => m.classList.remove('show'));
            document.querySelectorAll('.perfilado-menu').forEach(m => m.classList.remove('show'));
        }

        function applySort(key, direction) { currentSort = { key, direction }; renderTable(); }

        // Cache para coordenadas geocodificadas
        let geocodeCache = {};

// ═══ GEO/DISTANCE ═══════════════════════════════════════════════════════════
        async function geocodeAddress(address) {
            // Verificar cache
            if (geocodeCache[address]) {
                return geocodeCache[address];
            }

            try {
                const cleanAddress = address.replace(/OB\.\s*/i, '').trim() + ', España';
                const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(cleanAddress)}&format=json&limit=1`;
                const response = await fetch(url, {
                    headers: { 'User-Agent': 'GestorPedidos/1.0' }
                });
                const data = await response.json();
                
                if (data && data.length > 0) {
                    const coords = { lat: parseFloat(data[0].lat), lon: parseFloat(data[0].lon) };
                    geocodeCache[address] = coords;
                    return coords;
                }
            } catch (error) {
                console.error('Error geocodificando:', address, error);
            }
            return null;
        }

        function calculateDistance(lat1, lon1, lat2, lon2) {
            // Fórmula de Haversine para calcular distancia en km
            const R = 6371; // Radio de la Tierra en km
            const dLat = (lat2 - lat1) * Math.PI / 180;
            const dLon = (lon2 - lon1) * Math.PI / 180;
            const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                      Math.sin(dLon/2) * Math.sin(dLon/2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
            return R * c;
        }

        async function sortByDistance() {
            const origin = { lat: 40.9701, lon: -5.6635 }; // Salamanca, España
            
            // Mostrar mensaje de carga
            const body = document.getElementById('tableBody');
            body.innerHTML = '<tr><td colspan="100" class="text-center p-8 text-slate-400"><span class="material-symbols-outlined text-4xl animate-spin inline-block">progress_activity</span><br>Calculando distancias...</td></tr>';
            
            try {
                // Calcular distancias para todos los destinos únicos
                const uniqueDestinations = [...new Set(orders.map(o => o.destino).filter(d => d && d !== '-'))];
                const distancePromises = uniqueDestinations.map(async (dest) => {
                    const coords = await geocodeAddress(dest);
                    if (coords) {
                        const distance = calculateDistance(origin.lat, origin.lon, coords.lat, coords.lon);
                        return { destination: dest, distance };
                    }
                    return { destination: dest, distance: 999999 }; // Sin coordenadas al final
                });
                
                const distances = await Promise.all(distancePromises);
                const distanceMap = {};
                distances.forEach(d => distanceMap[d.destination] = d.distance);
                
                // Ordenar los pedidos por distancia
                orders.sort((a, b) => {
                    const distA = distanceMap[a.destino] || 999999;
                    const distB = distanceMap[b.destino] || 999999;
                    return distA - distB;
                });
                
                currentSort = { key: 'destino', direction: 'distance' };
                renderTable();
            } catch (error) {
                console.error('Error ordenando por distancia:', error);
                alert('Error al calcular distancias. Por favor, intenta de nuevo.');
                renderTable();
            }
        }

// ═══ FOLDER / FAVORITE / DATE HELPERS ═══════════════════════════════════════
        function getFolderColor(type) {
            const colors = { 'green': '#22c55e', 'yellow': '#eab308', 'orange': '#f97316', 'red': '#ef4444', 'blue': '#1886ed', 'pink': '#e30052' };
            return colors[type] || '#64748b';
        }

        function toggleFolderMenu(event, id) {
            event.stopPropagation();
            const all = document.querySelectorAll('.folder-menu');
            const target = document.getElementById(`folder-menu-${id}`);
            const isVisible = target.classList.contains('show');
            all.forEach(m => m.classList.remove('show'));
            if (!isVisible) target.classList.add('show');
        }

        function setFolder(id, color) {
            const index = orders.findIndex(o => o.id === id);
            if (index !== -1) { pushToHistory(); orders[index].folder = color; saveList(false); renderTable(); }
        }

        function parseDate(dateStr) {
            if (!dateStr) return 0;
            const parts = dateStr.split('/');
            return parts.length === 3 ? new Date(parts[2], parts[1] - 1, parts[0]).getTime() : 0;
        }

        function extractNumber(str) {
            if (typeof str !== 'string') return isNaN(str) ? 0 : str;
            const match = str.match(/\d+/);
            return match ? parseInt(match[0], 10) : 0;
        }

        function toggleFavorite(id) {
            const index = orders.findIndex(o => o.id === id);
            if (index !== -1) { pushToHistory(); orders[index].favorite = !orders[index].favorite; saveList(false); renderTable(); }
        }

        // Funciones auxiliares para obtener icono y color según estado

// ═══ STATUS ICON HELPERS ═════════════════════════════════════════════════════
        function getPrintedIcon(state) {
            if (state === 2) return 'print_connect'; // Impreso completo
            if (state === 1) return 'print_error'; // Impreso a medias
            return 'print_disabled'; // No impreso
        }

        function getPrintedColor(state) {
            if (state === 2) return 'text-green-500';
            if (state === 1) return 'text-orange-500';
            return 'text-red-500';
        }

        function getPrintedTitle(state) {
            if (state === 2) return 'Impreso';
            if (state === 1) return 'Impreso a medias';
            return 'No impreso';
        }

        function getSentIcon(state) {
            if (state === 2) return 'mark_email_read'; // Enviado completo
            if (state === 1) return 'forward_to_inbox'; // Enviado a medias
            return 'mail_off'; // No enviado
        }

        function getSentColor(state) {
            if (state === 2) return 'text-green-500';
            if (state === 1) return 'text-orange-500';
            return 'text-red-500';
        }

        function getSentTitle(state) {
            if (state === 2) return 'Enviado';
            if (state === 1) return 'Enviado a medias';
            return 'No enviado';
        }

        function getDeliveredIcon(state) {
            return state ? 'folder_check' : 'folder_off';
        }

        function getDeliveredColor(state) {
            return state ? 'text-green-500' : 'text-red-500';
        }

        function getDeliveredTitle(state) {
            return state ? 'Entregado' : 'No entregado';
        }

        // Funciones para el icono de tipo de registro (PEDIDO/OFERTA)
        function getTipoRegistroIcon(state) {
            return state === 1 ? 'real_estate_agent' : 'list_alt_check';
        }

        function getTipoRegistroColor(state) {
            return state === 1 ? '#FFFF55' : '#75FBFD';
        }

        function getTipoRegistroTitle(state) {
            return state === 1 ? 'OFERTA - Clic para cambiar a PEDIDO' : 'PEDIDO - Clic para cambiar a OFERTA';
        }

        function toggleTipoRegistro(id) {
            const index = orders.findIndex(o => o.id === id);
            if (index !== -1) {
                pushToHistory();
                orders[index].tipoRegistro = orders[index].tipoRegistro === 1 ? 0 : 1;
                saveList(false);
                renderTable();
            }
        }

        // Funciones para cambiar de modo PEDIDOS/OFERTAS

// ═══ MODE SWITCH ═════════════════════════════════════════════════════════════
        function setModoPedidos() {
            modoActual = 'pedidos';
            selectedRows.clear(); // Limpiar selección al cambiar de modo
            document.getElementById('modoPedidosBtn').className = 'modo-btn active-pedidos';
            document.getElementById('modoOfertasBtn').className = 'modo-btn inactive';
            renderHeaders();
            renderTable();
        }

        function setModoOfertas() {
            modoActual = 'ofertas';
            selectedRows.clear(); // Limpiar selección al cambiar de modo
            document.getElementById('modoPedidosBtn').className = 'modo-btn inactive';
            document.getElementById('modoOfertasBtn').className = 'modo-btn active-ofertas';
            renderHeaders();
            renderTable();
        }

        // Función para actualizar la revisión

// ═══ REVISION ════════════════════════════════════════════════════════════════
        function updateRevision(id, value) {
            const index = orders.findIndex(o => o.id === id);
            if (index !== -1) {
                pushToHistory();
                const parsed = parseInt(value);
                const newRevision = isNaN(parsed) ? 0 : parsed;
                orders[index].revision = newRevision;
                
                // Actualizar la fecha de la revisión si no existe
                if (newRevision > 0) {
                    if (!orders[index].fechasRev) orders[index].fechasRev = {};
                    if (!orders[index].fechasRev[newRevision]) {
                        orders[index].fechasRev[newRevision] = new Date().toLocaleDateString('es-ES');
                    }
                }
                
                // Si es una OFERTA (tipoRegistro === 1) y la revisión es >= 1, asignar color rojo
                if (orders[index].tipoRegistro === 1 && newRevision >= 1) {
                    orders[index].folder = 'red';
                }
                
                saveList(false);
                renderTable();
            }
        }

        // Función para actualizar las notas de una revisión específica
        function updateNotasRev(id, value) {
            const index = orders.findIndex(o => o.id === id);
            if (index !== -1) {
                const rev = orders[index].revision || 0;
                if (!orders[index].notasRev) orders[index].notasRev = {};
                
                const oldValue = orders[index].notasRev[rev] || '';
                const newValue = value.trim();
                
                if (oldValue !== newValue) {
                    pushToHistory();
                    orders[index].notasRev[rev] = newValue;
                    saveList(false);
                }
            }
        }

        // Función para marcar/desmarcar REV como hecha
        function toggleRevHecha(id) {
            const index = orders.findIndex(o => o.id === id);
            if (index !== -1) {
                const rev = orders[index].revision || 0;
                if (rev === 0) return; // No hacer nada si no hay REV seleccionada
                
                if (!orders[index].revHecha) orders[index].revHecha = {};
                
                pushToHistory();
                orders[index].revHecha[rev] = !orders[index].revHecha[rev];
                saveList(false);
                renderTable();
            }
        }

        // Función para obtener si la REV actual está hecha
        function isRevHecha(item) {
            const rev = item.revision || 0;
            if (rev === 0) return false;
            return item.revHecha && item.revHecha[rev];
        }

        // Función para obtener la fecha de una revisión específica
        function getFechaRev(item) {
            const rev = item.revision || 0;
            if (rev === 0) return item.fecha; // Si no hay revisión, mostrar fecha original
            if (item.fechasRev && item.fechasRev[rev]) {
                return item.fechasRev[rev];
            }
            return item.fecha; // Fallback a fecha original
        }

        // Función para obtener el número de oferta sin "OF "
        function getOfertaNumero(oferta) {
            if (!oferta) return '-';
            return oferta.replace(/^OF\s*/i, '').trim();
        }


// ═══ TOGGLE PRINTED/SENT/DELIVERED ══════════════════════════════════════════
        function togglePrinted(id) {
            const index = orders.findIndex(o => o.id === id);
            if (index !== -1) { 
                pushToHistory(); 
                // Ciclar entre 0 -> 1 -> 2 -> 0
                orders[index].printed = (orders[index].printed + 1) % 3;
                saveList(false); 
                renderTable(); 
            }
        }

        function toggleSent(id) {
            const index = orders.findIndex(o => o.id === id);
            if (index !== -1) { 
                pushToHistory(); 
                // Ciclar entre 0 -> 1 -> 2 -> 0
                orders[index].sent = (orders[index].sent + 1) % 3;
                saveList(false); 
                renderTable(); 
            }
        }

        function toggleDelivered(id) {
            const index = orders.findIndex(o => o.id === id);
            if (index !== -1) { 
                pushToHistory(); 
                orders[index].delivered = !orders[index].delivered; 
                saveList(false); 
                renderTable(); 
            }
        }


// ═══ COPY / FOLDER PATH ═════════════════════════════════════════════════════
        function copyToClipboard(e, id) {
            const item = orders.find(o => o.id === id);
            if (!item) return;
            
            let textToCopy = '';
            
            if (modoActual === 'ofertas') {
                // MODO OFERTAS: Solo FECHA, OFERTA, REV, CLIENTE, NOTAS
                const currentRev = item.revision || 0;
                const revText = currentRev === 0 ? '-' : `REV ${currentRev}`;
                const currentNota = (item.notasRev && item.notasRev[currentRev]) || '-';
                textToCopy = `Fecha: ${item.fecha} | Oferta: ${getOfertaNumero(item.oferta)} | ${revText} | Cliente: ${item.cliente} | Notas: ${currentNota}`;
            } else {
                // MODO PEDIDOS: Todas las columnas
                const panel = item.panelGrosor && item.panelTipo ? `${item.panelGrosor} ${item.panelTipo}` : (item.panelGrosor || item.panelTipo || '-');
                const hBase = calcularHBase(item.l, item.a, item.base, item.panelGrosor);
                const hCubierta = calcularHCubierta(item.l, item.a, item.base, item.panelGrosor, item.cubierta);
                const pilar = calcularPilar(item.a, item.panelGrosor);
                const estructura = `H.Base: ${hBase} / H.Cubierta: ${hCubierta} / Pilar: ${pilar}`;
                const colorPanel = item.colorPanel || '-';
                const colorEstructura = item.colorEstructura || '-';
                const colorCarpinteria = item.colorCarpinteria || '-';
                textToCopy = `Fecha: ${item.fecha} | Oferta: ${getOfertaNumero(item.oferta)} | N/P: ${item.numPedido || '-'} | Cliente: ${item.cliente} | Destino: ${item.destino} | Serie: ${item.serie} | Medidas: ${item.l}x${item.a}x${item.h} | Estructura: ${estructura} | Panel: ${panel} | Base: ${item.base || '-'} | Acabado: ${item.acabado || '-'} | Suministro: ${item.suministro || '-'} | Perfilado: ${item.perfilado || '-'} | Color Panel: ${colorPanel} | Color Estructura: ${colorEstructura} | Color Carpintería: ${colorCarpinteria} | Notas: ${item.extra}`;
            }
            
            const helper = document.getElementById('copyHelper');
            helper.value = textToCopy; helper.select(); document.execCommand('copy');
            const icon = e.currentTarget.querySelector('.material-symbols-outlined');
            const originalText = icon.innerText; icon.innerText = 'check'; icon.classList.add('copied-feedback');
            setTimeout(() => { icon.innerText = originalText; icon.classList.remove('copied-feedback'); }, 1500);
        }

        function openPedidoFolder(id) {
            const item = orders.find(o => o.id === id);
            if (!item) return;

            // Crear contenido del modal con input y botón
            const currentPath = item.folderPath || '';
            const modalContent = `
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-2">Ruta de la carpeta:</label>
                        <input 
                            type="text" 
                            id="folderPathInput" 
                            value="${currentPath}" 
                            placeholder="Ej: C:\\Pedidos\\OF00105\\ o http://..." 
                            class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:border-blue-500"
                        />
                    </div>
                    ${currentPath ? `
                    <button 
                        onclick="window.open(document.getElementById('folderPathInput').value, '_blank')" 
                        class="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors flex items-center justify-center gap-2"
                    >
                        <span class="material-symbols-outlined text-sm">open_in_new</span>
                        Abrir Carpeta
                    </button>
                    ` : ''}
                </div>
            `;

            const titleElement = document.getElementById('modalTitle');
            titleElement.innerText = 'Carpeta del Pedido';
            titleElement.className = 'text-xl font-bold mb-4 text-white';
            
            document.getElementById('modalDesc').innerHTML = modalContent;
            
            const container = document.getElementById('modalButtons');
            container.innerHTML = `
                <button onclick="saveFolderPath(${id})" class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded transition-colors">
                    Guardar
                </button>
                <button onclick="closeModal()" class="px-4 py-2 bg-slate-600 hover:bg-slate-700 text-white rounded transition-colors">
                    Cancelar
                </button>
            `;
            
            modal.style.display = 'flex';
            
            // Focus en el input
            setTimeout(() => {
                const input = document.getElementById('folderPathInput');
                if (input) input.focus();
            }, 100);
        }

        function saveFolderPath(id) {
            const input = document.getElementById('folderPathInput');
            if (!input) return;
            
            const newPath = input.value.trim();
            const index = orders.findIndex(o => o.id === id);
            if (index !== -1) {
                pushToHistory();
                orders[index].folderPath = newPath;
                saveList(false);
                renderTable();
            }
            closeModal();
        }


// ═══ HISTORY / SAVE ══════════════════════════════════════════════════════════
        function pushToHistory() {
            const _serialized = JSON.stringify(orders);
            if (history.length > 0 && history[history.length - 1] === _serialized) return;
            history.push(_serialized);
            if (history.length > 50) history.shift();
            document.getElementById('undoBtn').disabled = false;
        }

        function undoLastAction() {
            if (history.length === 0) return;
            orders = JSON.parse(history.pop());
            if (history.length === 0) document.getElementById('undoBtn').disabled = true;
            saveList(false); renderTable();
        }

        function saveList(withHistory = true) {
            if (withHistory) pushToHistory();
            localStorage.setItem('fabricacion_orders', JSON.stringify(orders));
            showSaveStatus();
        }

        function manualSave() { saveList(false); }
        function showSaveStatus() {
            const status = document.getElementById('saveStatus');
            status.style.opacity = '1';
            setTimeout(() => status.style.opacity = '0', 2000);
        }

// ═══ CELL NAVIGATION ════════════════════════════════════════════════════════
        // Variables para navegación con Enter
        let pendingFocus = null;

        // Manejar navegación con Enter en celdas editables (delegación de eventos)
        function handleCellKeydown(event) {
            const cell = event.target;
            if (cell.tagName === 'TD' && cell.contentEditable === 'true' && event.key === 'Enter') {
                event.preventDefault();
                event.stopPropagation();
                
                const currentRow = cell.closest('tr');
                const rowId = currentRow.dataset.id;
                
                // Buscar la siguiente celda editable en la MISMA FILA
                const rowEditableCells = Array.from(currentRow.querySelectorAll('td[contenteditable="true"]'));
                const currentIndex = rowEditableCells.indexOf(cell);
                
                // Guardar info para enfocar después del posible renderTable
                if (currentIndex !== -1 && currentIndex < rowEditableCells.length - 1) {
                    pendingFocus = {
                        rowId: rowId,
                        cellIndex: currentIndex + 1
                    };
                } else {
                    pendingFocus = null;
                }
                
                // Disparar blur para guardar el valor actual
                cell.blur();
                
                // Si no hay renderTable pendiente, enfocar inmediatamente
                setTimeout(() => {
                    if (pendingFocus) {
                        focusPendingCell();
                    }
                }, 50);
            }
        }

        // Función para enfocar celda pendiente (llamada después de renderTable o por timeout)
        function focusPendingCell() {
            if (pendingFocus) {
                const row = document.querySelector(`tr[data-id="${pendingFocus.rowId}"]`);
                if (row) {
                    const cells = Array.from(row.querySelectorAll('td[contenteditable="true"]'));
                    const targetCell = cells[pendingFocus.cellIndex];
                    if (targetCell) {
                        targetCell.focus();
                        // Seleccionar todo el contenido
                        const range = document.createRange();
                        range.selectNodeContents(targetCell);
                        const selection = window.getSelection();
                        selection.removeAllRanges();
                        selection.addRange(range);
                    }
                }
                pendingFocus = null;
            }
        }

        // Inicializar delegación de eventos para keydown en tbody
        function initCellNavigation() {
            const tbody = document.getElementById('tableBody');
            tbody.addEventListener('keydown', handleCellKeydown);
            // Delegated hover highlight (opt. 2) — set up once, works for all modes
            tbody.addEventListener('mouseenter', (e) => {
                const row = e.target.closest('tr');
                if (row) row.querySelectorAll('td').forEach(td => td.classList.add('row-hover-td'));
            }, true);
            tbody.addEventListener('mouseleave', (e) => {
                const row = e.target.closest('tr');
                if (row) row.querySelectorAll('td.row-hover-td').forEach(td => td.classList.remove('row-hover-td'));
            }, true);
        }

// ═══ DATA UPDATE FUNCTIONS ══════════════════════════════════════════════════
        function kitVariant(item) {
            // Sin panel → E80 (solo estructura)
            if (!item.panelGrosor || !parseInt(item.panelGrosor)) return 'E80';
            const l = parseInt(item.l) || 0;
            if (l >= 6000) return 'E90';
            if (l >= 5000) return 'E230';
            if (l >= 4000) return 'E270';
            if (l >= 3000) return 'E290';
            return 'E80 P';  // < 3000mm — paletizado
        }

        function updateValue(id, key, value) {
            const index = orders.findIndex(o => o.id === id);
            if (index !== -1) {
                const oldValue = orders[index][key];
                const newValue = value.trim();
                
                if (oldValue !== newValue) {
                    pushToHistory(); 
                    orders[index][key] = newValue;
                    localStorage.setItem('fabricacion_orders', JSON.stringify(orders));
                    showSaveStatus(); 
                }
                
                // Si se modifica L, A, BASE, panelGrosor o suministro, recalcular tabla
                if (key === 'l' || key === 'a' || key === 'base' || key === 'panelGrosor' || key === 'suministro') {
                    renderTable();
                }
            }
        }

        function updateCubierta(id, value) {
            const index = orders.findIndex(o => o.id === id);
            if (index !== -1) {
                pushToHistory();
                orders[index].cubierta = value;
                saveList(false);
                renderTable();
            }
        }

        function updatePanelCombinado(id, value) {
            const index = orders.findIndex(o => o.id === id);
            if (index !== -1) {
                pushToHistory();
                if (value === '') {
                    orders[index].panelGrosor = '';
                    orders[index].panelTipo = '';
                } else {
                    const [grosor, tipo] = value.split('|');
                    orders[index].panelGrosor = grosor;
                    orders[index].panelTipo = tipo;
                }
                saveList(false);
                renderTable();
            }
        }

        function calcularHBase(l, a, base, panelGrosor) {
            const longitud = parseInt(l) || 0;
            const anchura = parseInt(a) || 0;
            const tipoBase = (base || "").toUpperCase().trim();
            const panel = parseInt(panelGrosor) || 0;
            
            if (longitud === 0) return "-";
            
            // BASE HORMIGONADA (con UPN)
            if (tipoBase === "HORMIGONADA") {
                if (longitud <= 7000) return "UPN 140";
                if (longitud >= 7001) return "UPN 160";
            }
            
            // BASE TRAMEX (BANDEJA TRAMEX - BASE ALT. ESPECIAL)
            if (tipoBase === "TRAMEX") {
                return 200;
            }

            // BASE SANEAMIENTO (BASE ALT. ESPECIAL)
            if (tipoBase === "SANEAMIENTO") {
                return 240;
            }
            
            // Para las demás bases (TABLERO): HIDRÓFUGO, FENÓLICO, FIBROCEMENTO, etc.

            // Cálculo base según longitud
            let valorBase;
            if (longitud <= 6000) valorBase = 137;
            else if (longitud <= 7000) valorBase = 160;
            else if (longitud <= 8500) valorBase = 160;
            else valorBase = 200;

            // Carril >e60 (panel >60mm): BASE mínimo 160
            if (panel > 60) {
                valorBase = Math.max(valorBase, 160);
            }

            // Regla especial: ANCHO > 2500mm = MÍNIMO 160
            if (anchura > 2500) {
                valorBase = Math.max(valorBase, 160);
            }

            return valorBase;
        }

        function calcularHCubierta(l, a, base, panelGrosor, cubierta) {
            const longitud = parseInt(l) || 0;
            const anchura = parseInt(a) || 0;
            const tipoBase = (base || "").toUpperCase().trim();
            const panel = parseInt(panelGrosor) || 0;
            const tipoCubierta = (cubierta || "").toUpperCase().trim();
            
            if (longitud === 0) return "-";
            
            // Regla: Si CUBIERTA es PANEL → BASTIDOR CUBIERTA siempre 165
            if (tipoCubierta === "PANEL") {
                return 165;
            }
            
            // BASE HORMIGONADA
            if (tipoBase === "HORMIGONADA") {
                if (longitud <= 7000) return 160;
                if (longitud >= 7001) return 190;
            }
            
            // BASE TRAMEX (BANDEJA TRAMEX - BASE ALT. ESPECIAL) = MÍNIMO 160
            if (tipoBase === "TRAMEX") {
                return 160;
            }

            // BASE SANEAMIENTO (BASE ALT. ESPECIAL) = MÍNIMO 160
            if (tipoBase === "SANEAMIENTO") {
                return 160;
            }
            
            // Calcular valor base según longitud (BASE TABLERO)
            let valorCubierta = 129;
            if (longitud <= 6000) valorCubierta = 129;
            else if (longitud >= 6001 && longitud <= 7000) valorCubierta = 160;
            else if (longitud >= 7001 && longitud <= 8500) valorCubierta = 190;
            else if (longitud >= 8501) valorCubierta = 190;
            
            // Regla: Panel > 40mm = MÍNIMO 160
            if (panel > 40) {
                valorCubierta = Math.max(valorCubierta, 160);
            }
            
            // Regla especial: Cualquier LONGITUD y ANCHO > 2500mm = MÍNIMO 160
            if (anchura > 2500) {
                valorCubierta = Math.max(valorCubierta, 160);
            }
            
            return valorCubierta;
        }

        function calcularCorreas(l, a, base, panelGrosor, cubierta) {
            const _ck = `${l}|${a}|${base}|${panelGrosor}|${cubierta}`;
            if (_correasCache.has(_ck)) return _correasCache.get(_ck);
            const _cache = (v) => { _correasCache.set(_ck, v); return v; };
            const esPanel = (cubierta || '').toUpperCase().trim() === 'PANEL';
            const tipoBase = (base || '').toUpperCase().trim();
            const esHormigonada = tipoBase === 'HORMIGONADA';
            if (esPanel) return _cache({ lineas: [], corner: true });
            const longitud = parseInt(l) || 0;
            const hCubierta = calcularHCubierta(l, a, base, panelGrosor, cubierta);
            const h = parseInt(hCubierta) || 0;
            const anchura = parseInt(a) || 0;
            if (longitud === 0 || h === 0 || isNaN(h)) return _cache(null);

            // "Todos los módulos con base hormigón llevarán dado tipo CORNER sea cual sea su altura y dimensión"

            // Tabla H=129 (*)
            if (h === 129) {
                if (longitud <= 2300) return _cache({ lineas: ['1x50','2x40'], corner: esHormigonada });
                if (longitud <= 3000) return _cache({ lineas: ['1x50','2x40'], corner: esHormigonada });
                if (longitud <= 4000) return _cache({ lineas: ['3x50','2x40'], corner: esHormigonada });
                if (longitud <= 5000) return _cache({ lineas: ['3x50','2x40'], corner: esHormigonada });
                if (longitud <= 6000) return _cache({ lineas: ['3x50','4x40'], corner: esHormigonada });
                return _cache(null); // >6000 no aplica H=129
            }

            // Tabla H=160 (*)
            if (h === 160) {
                if (longitud <= 2300) return _cache({ lineas: ['1x50','2x40'], corner: esHormigonada });
                if (longitud <= 3000) return _cache({ lineas: ['1x50','2x40'], corner: esHormigonada });
                if (longitud <= 4000) return _cache({ lineas: ['3x50','2x40'], corner: esHormigonada });
                if (longitud <= 5000) return _cache({ lineas: ['3x50','2x40'], corner: esHormigonada });
                if (longitud <= 6000) return _cache({ lineas: ['3x60','2x50','2x40'], corner: esHormigonada });
                if (longitud <= 7000) return _cache({ lineas: ['4x60','2x50','2x40'], corner: true });
                return _cache(null); // >7000 no aplica H=160
            }

            // Tabla H=165 (CUBIERTA PANEL) / H=190 (**)
            if (h >= 165) {
                if (longitud <= 2300) return _cache({ lineas: ['1x60','2x50'], corner: true });
                if (longitud <= 3000) return _cache({ lineas: ['1x60','2x50'], corner: true });
                if (longitud <= 4000) return _cache({ lineas: ['1x75','2x60','2x50'], corner: true });
                if (longitud <= 5000) return _cache({ lineas: ['1x75','2x60','2x50'], corner: true });
                if (longitud <= 6000) return _cache({ lineas: ['3x75','2x60','2x50'], corner: true });
                if (longitud <= 7000) return _cache({ lineas: ['4x75','2x60','2x50'], corner: true });
                if (longitud <= 8000) return _cache({ lineas: ['3x90','2x75','4x60'], corner: true });
                return _cache({ lineas: ['3x90','2x75','4x60'], corner: true }); // >8000
            }

            return _cache(null);
        }

        function renderCorreas(l, a, base, panelGrosor, cubierta) {
            const result = calcularCorreas(l, a, base, panelGrosor, cubierta);
            if (!result) return '<span class="text-slate-500 text-xs">-</span>';

            const esPanel = (cubierta || '').toUpperCase().trim() === 'PANEL';
            const esHormigonada = (base || '').toUpperCase().trim() === 'HORMIGONADA';

            // Badge a mostrar: si es PANEL → nada; si es hormigonada → DADO; si es corner normal → CORNER
            function getBadge(marginTop) {
                const mt = marginTop ? 'margin-top:3px;' : '';
                if (esPanel) return '';
                if (esHormigonada) {
                    return `<span style="display:inline-block;${mt}padding:1px 5px;border-radius:3px;background:rgba(139,92,246,0.15);border:1px solid rgba(139,92,246,0.4);color:#c4b5fd;font-size:9px;font-weight:700;letter-spacing:0.05em;">DADO</span>`;
                }
                if (result.corner) {
                    return `<span style="display:inline-block;${mt}padding:1px 5px;border-radius:3px;background:rgba(139,92,246,0.15);border:1px solid rgba(139,92,246,0.4);color:#c4b5fd;font-size:9px;font-weight:700;letter-spacing:0.05em;">DADO</span>`;
                }
                return '';
            }

            if (result.lineas.length === 0) {
                return `<div style="display:flex;flex-direction:column;align-items:center;gap:2px;"><span style="color:#94a3b8;font-size:10px;font-style:italic;">sin correas</span>${getBadge(false)}</div>`;
            }

            const anchura = parseInt(a) || 0;
            const anchoGrande = anchura > 2500;

            const lineasHTML = result.lineas.map(linea => {
                const isCorner = result.corner;
                const bg = isCorner ? 'background:rgba(234,179,8,0.2); border:1px solid rgba(234,179,8,0.5);' : 'background:rgba(100,116,139,0.2); border:1px solid rgba(100,116,139,0.3);';
                const color = isCorner ? 'color:#fbbf24;' : 'color:#cbd5e1;';
                return `<span style="display:inline-block;padding:1px 5px;border-radius:4px;font-family:'Courier New',monospace;font-size:11px;font-weight:700;${bg}${color}">${linea}</span>`;
            }).join(' ');

            const cornerTag = getBadge(true);

            const anchoTag = anchoGrande
                ? `<span style="display:inline-block;margin-top:3px;padding:1px 5px;border-radius:3px;background:rgba(239,68,68,0.15);border:1px solid rgba(239,68,68,0.4);color:#fca5a5;font-size:9px;font-weight:700;">REF +600</span>`
                : '';

            return `<div style="display:flex;flex-direction:column;align-items:center;gap:2px;">${lineasHTML}<div style="display:flex;gap:3px;">${cornerTag}${anchoTag}</div></div>`;
        }

        function calcularPilar(a, panelGrosor) {
            const anchura = parseInt(a) || 0;
            const grosor = parseInt(panelGrosor) || 0;
            
            // Si no hay anchura definida
            if (anchura === 0) return "-";
            
            // Si el espesor del panel es 100mm (independiente de la anchura)
            if (grosor === 100) return "245x217";
            
            // Según el ancho del módulo
            if (anchura === 1190) return "125x125";
            if (anchura === 2400) return "220x167";
            if (anchura === 2440) return "240x167";
            
            // Si A <= 2350 o cualquier otra medida
            return "195x167";
        }

        function getModuloStyle(modulo) {
            const colors = {
                'M1': 'background:rgba(99,102,241,0.2);border:1px solid rgba(99,102,241,0.5);color:#a5b4fc;',
                'M2': 'background:rgba(16,185,129,0.2);border:1px solid rgba(16,185,129,0.5);color:#6ee7b7;',
                'M3': 'background:rgba(245,158,11,0.2);border:1px solid rgba(245,158,11,0.5);color:#fcd34d;',
                'M4': 'background:rgba(239,68,68,0.2);border:1px solid rgba(239,68,68,0.5);color:#fca5a5;',
            };
            return colors[modulo] || colors['M1'];
        }

        function cycleModulo(id) {
            const index = orders.findIndex(o => o.id === id);
            if (index === -1) return;
            pushToHistory();
            const cycle = ['M1','M2','M3','M4'];
            const current = orders[index].modulo || 'M1';
            const next = cycle[(cycle.indexOf(current) + 1) % cycle.length];
            orders[index].modulo = next;
            saveList(false);
            renderTable();
        }

        // ── Vinculación de adosamiento ────────────────────────────────────────────
        function toggleConjuntoVinculado(id) {
            const index = orders.findIndex(o => o.id === id);
            if (index === -1) return;
            pushToHistory();
            orders[index].conjuntoVinculado = !orders[index].conjuntoVinculado;
            // Limpiar adosamiento al cambiar modo para que se reconfigure
            orders[index].adosamiento = null;
            saveList(false);
            renderTable();
        }

        function toggleConjunto(id) {
            const index = orders.findIndex(o => o.id === id);
            if (index === -1) return;
            pushToHistory();
            orders[index].conjunto = !orders[index].conjunto;
            if (!orders[index].conjunto) {
                // Pasa a AISLADO: limpiar vinculación y adosamiento
                orders[index].conjuntoVinculado = false;
                orders[index].adosamiento       = null;
            }
            saveList(false);
            renderTable();
        }

        function duplicateRow(id) {
            const source = orders.find(o => o.id === id);
            if (!source) return;

            const container = document.getElementById('modalButtons');
            document.getElementById('modalTitle').innerText = 'Duplicar fila';
            document.getElementById('modalDesc').innerHTML = `
                <div class="flex flex-col gap-3 mt-2">
                    <button onclick="doAddModulo(${id})" class="w-full px-4 py-3 text-sm font-bold bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-colors text-left flex items-center gap-3">
                        <span class="material-symbols-outlined">account_tree</span>
                        <div>
                            <div>Añadir módulo al pedido</div>
                            <div class="font-normal text-xs text-cyan-200 mt-0.5">Nueva fila M2/M3… con L·A·H en blanco, mismo pedido</div>
                        </div>
                    </button>
                    <button onclick="doReplicarPedido(${id})" class="w-full px-4 py-3 text-sm font-bold bg-slate-600 hover:bg-slate-500 text-white rounded-lg transition-colors text-left flex items-center gap-3">
                        <span class="material-symbols-outlined">content_copy</span>
                        <div>
                            <div>Replicar pedido</div>
                            <div class="font-normal text-xs text-slate-300 mt-0.5">Copia exacta como pedido independiente (M1)</div>
                        </div>
                    </button>
                </div>`;
            container.innerHTML = `<button onclick="closeModal()" class="px-4 py-2 text-sm text-slate-400">Cancelar</button>`;
            modal.style.display = 'flex';
        }

        function doAddModulo(id) {
            closeModal();
            const source = orders.find(o => o.id === id);
            if (!source) return;
            pushToHistory();
            const siblingsModulos = orders
                .filter(o => o.oferta === source.oferta && o.numPedido === source.numPedido && o.cliente === source.cliente)
                .map(o => o.modulo || 'M1');
            const cycle = ['M1','M2','M3','M4','M5','M6'];
            let nextModulo = 'M2';
            for (const m of cycle) {
                if (!siblingsModulos.includes(m)) { nextModulo = m; break; }
            }
            const newOrder = {
                ...source,
                id: Date.now() + Math.floor(Math.random() * 1000),
                modulo: nextModulo,
                serie: '-',
                l: '0', a: '0', h: '0',
            };
            const idx = orders.findIndex(o => o.id === id);
            // Insertar al final del grupo
            let insertAt = idx + 1;
            while (insertAt < orders.length &&
                   orders[insertAt].oferta === source.oferta &&
                   orders[insertAt].numPedido === source.numPedido &&
                   orders[insertAt].cliente === source.cliente) {
                insertAt++;
            }
            orders.splice(insertAt, 0, newOrder);
            saveList(false);
            renderTable();
        }

        function doReplicarPedido(id) {
            closeModal();
            const source = orders.find(o => o.id === id);
            if (!source) return;
            pushToHistory();
            const newOrder = {
                ...source,
                id: Date.now() + Math.floor(Math.random() * 1000),
                modulo: 'M1',
            };
            const idx = orders.findIndex(o => o.id === id);
            orders.splice(idx + 1, 0, newOrder);
            saveList(false);
            renderTable();
        }

        function addNewRow() {
            // Determinar el tipoRegistro según el modo actual
            const tipoReg = modoActual === 'ofertas' ? 1 : 0;
            const newOrder = { 
                id: Date.now(), fecha: new Date().toLocaleDateString('es-ES'), oferta: "OF ---/26", numPedido: "", cliente: "NUEVO", destino: "-", serie: "-", l: "0", a: "0", h: "0", estBase: "", estCubierta: "", estPilar: "", panelGrosor: "", panelTipo: "", cantidad: 1, modulo: "M1", conjunto: false, conjuntoVinculado: false, adosamiento: null, cubierta: "", base: "", acabado: "", suministro: "", perfilado: "", colorPanel: "", colorEstructura: "", colorCarpinteria: "", extra: "", folderPath: "", printed: 0, sent: 0, delivered: 0, tipoRegistro: tipoReg, revision: 0, revHecha: {}, notasRev: {}, fechasRev: {}, favorite: false, folder: null
            };
            pushToHistory(); orders.unshift(newOrder); saveList(false); renderTable();
        }
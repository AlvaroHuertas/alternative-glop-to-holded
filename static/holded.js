// Holded Queries Script

// DOM Elements
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const statusMessage = document.getElementById('statusMessage');

// Holded Warehouses Section
const fetchWarehousesBtn = document.getElementById('fetchWarehousesBtn');
const holdedWarehousesSection = document.getElementById('holdedWarehousesSection');
const toggleHoldedWarehousesBtn = document.getElementById('toggleHoldedWarehousesBtn');
const holdedWarehousesHeaderToggle = document.getElementById('holdedWarehousesHeaderToggle');
const clearHoldedWarehousesBtn = document.getElementById('clearHoldedWarehousesBtn');
const warehousesTableBody = document.getElementById('warehousesTableBody');
const warehousesCount = document.getElementById('warehousesCount');

// Stock by Warehouse Section
const fetchStockByWarehouseBtn = document.getElementById('fetchStockByWarehouseBtn');
const stockByWarehouseSection = document.getElementById('stockByWarehouseSection');
const toggleStockByWarehouseBtn = document.getElementById('toggleStockByWarehouseBtn');
const stockByWarehouseHeaderToggle = document.getElementById('stockByWarehouseHeaderToggle');
const clearStockByWarehouseBtn = document.getElementById('clearStockByWarehouseBtn');
const stockByWarehouseTableHead = document.getElementById('stockByWarehouseTableHead');
const stockByWarehouseTableBody = document.getElementById('stockByWarehouseTableBody');
const stockWarehousesCount = document.getElementById('stockWarehousesCount');
const stockProductsCount = document.getElementById('stockProductsCount');
const stockVariantsCount = document.getElementById('stockVariantsCount');

let isHoldedWarehousesCollapsed = false;
let isStockByWarehouseCollapsed = false;

// Show status message
function showStatus(message, type = 'success') {
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
    statusMessage.style.display = 'block';
}

// Hide status message
function hideStatus() {
    statusMessage.style.display = 'none';
}

// Update progress
function updateProgress(percent) {
    progressFill.style.width = `${percent}%`;
    progressText.textContent = `${percent}%`;
}

// =====================
// Warehouses Section
// =====================

// Toggle Holded warehouses section visibility
function toggleHoldedWarehouses() {
    isHoldedWarehousesCollapsed = !isHoldedWarehousesCollapsed;
    holdedWarehousesSection.classList.toggle('collapsed', isHoldedWarehousesCollapsed);
}

// Add click handlers for holded warehouses toggle
toggleHoldedWarehousesBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleHoldedWarehouses();
});

holdedWarehousesHeaderToggle.addEventListener('click', (e) => {
    if (!e.target.closest('.clear-btn')) {
        toggleHoldedWarehouses();
    }
});

// Clear holded warehouses data
clearHoldedWarehousesBtn.addEventListener('click', () => {
    holdedWarehousesSection.style.display = 'none';
    warehousesTableBody.innerHTML = '';
    warehousesCount.textContent = '0';
});

// Render warehouses table
function renderWarehouses(data) {
    warehousesTableBody.innerHTML = '';
    
    if (!data.warehouses || data.warehouses.length === 0) {
        const tr = document.createElement('tr');
        tr.innerHTML = '<td colspan="3" style="text-align: center; color: var(--text-secondary);">No hay almacenes disponibles</td>';
        warehousesTableBody.appendChild(tr);
        warehousesCount.textContent = '0';
        return;
    }
    
    data.warehouses.forEach(warehouse => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="numeric">${warehouse.id || '-'}</td>
            <td>${warehouse.name || '-'}</td>
            <td>${warehouse.desc || '-'}</td>
        `;
        warehousesTableBody.appendChild(tr);
    });
    
    warehousesCount.textContent = data.count.toLocaleString();
    
    // Show section and ensure it's expanded
    holdedWarehousesSection.style.display = 'block';
    holdedWarehousesSection.classList.remove('collapsed');
    isHoldedWarehousesCollapsed = false;
    
    // Scroll to section
    setTimeout(() => {
        holdedWarehousesSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 300);
}

// Fetch Holded warehouses
fetchWarehousesBtn.addEventListener('click', async () => {
    // Show progress
    progressContainer.style.display = 'block';
    fetchWarehousesBtn.disabled = true;
    hideStatus();

    try {
        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 10;
            if (progress <= 90) {
                updateProgress(progress);
            }
        }, 100);

        const response = await fetch('/api/holded/warehouses');

        clearInterval(progressInterval);
        updateProgress(100);

        if (response.ok) {
            const result = await response.json();
            showStatus(`¡Consulta exitosa! ${result.count} almacenes encontrados`, 'success');
            
            // Render warehouses
            renderWarehouses(result);
            
            // Hide progress after delay
            setTimeout(() => {
                progressContainer.style.display = 'none';
            }, 1500);
            
            fetchWarehousesBtn.disabled = false;
        } else {
            const error = await response.json();
            showStatus(error.detail || 'Error al obtener almacenes de Holded', 'error');
            fetchWarehousesBtn.disabled = false;
            progressContainer.style.display = 'none';
        }
    } catch (error) {
        console.error('Fetch warehouses error:', error);
        showStatus('Error de conexión. Por favor, intenta nuevamente.', 'error');
        fetchWarehousesBtn.disabled = false;
        progressContainer.style.display = 'none';
    }
});

// =====================
// Stock by Warehouse Section
// =====================

// Toggle stock by warehouse section visibility
function toggleStockByWarehouse() {
    isStockByWarehouseCollapsed = !isStockByWarehouseCollapsed;
    stockByWarehouseSection.classList.toggle('collapsed', isStockByWarehouseCollapsed);
}

// Add click handlers for stock by warehouse toggle
toggleStockByWarehouseBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleStockByWarehouse();
});

stockByWarehouseHeaderToggle.addEventListener('click', (e) => {
    if (!e.target.closest('.clear-btn')) {
        toggleStockByWarehouse();
    }
});

// Clear stock by warehouse data
clearStockByWarehouseBtn.addEventListener('click', () => {
    stockByWarehouseSection.style.display = 'none';
    stockByWarehouseTableHead.innerHTML = '';
    stockByWarehouseTableBody.innerHTML = '';
    stockWarehousesCount.textContent = '0';
    stockProductsCount.textContent = '0';
    stockVariantsCount.textContent = '0';
});

// Render stock by warehouse table
function renderStockByWarehouse(data) {
    // Clear existing content
    stockByWarehouseTableHead.innerHTML = '';
    stockByWarehouseTableBody.innerHTML = '';
    
    if (!data.warehouses || data.warehouses.length === 0) {
        const tr = document.createElement('tr');
        tr.innerHTML = '<td colspan="100%" style="text-align: center; color: var(--text-secondary);">No hay almacenes disponibles</td>';
        stockByWarehouseTableBody.appendChild(tr);
        stockWarehousesCount.textContent = '0';
        stockProductsCount.textContent = '0';
        stockVariantsCount.textContent = '0';
        return;
    }
    
    // Create header row: SKU | Producto | Warehouse1 | Warehouse2 | ...
    const headerRow = document.createElement('tr');
    
    const skuHeader = document.createElement('th');
    skuHeader.textContent = 'SKU';
    headerRow.appendChild(skuHeader);
    
    const nameHeader = document.createElement('th');
    nameHeader.textContent = 'Producto';
    headerRow.appendChild(nameHeader);
    
    // Add one column per warehouse
    data.warehouses.forEach(warehouse => {
        const whHeader = document.createElement('th');
        whHeader.className = 'numeric';
        whHeader.textContent = warehouse.name;
        whHeader.title = `ID: ${warehouse.id}`;
        headerRow.appendChild(whHeader);
    });
    
    stockByWarehouseTableHead.appendChild(headerRow);
    
    // Render data rows
    if (!data.products || data.products.length === 0) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td colspan="${2 + data.warehouses.length}" style="text-align: center; color: var(--text-secondary);">No hay productos con SKU</td>`;
        stockByWarehouseTableBody.appendChild(tr);
    } else {
        data.products.forEach(product => {
            const tr = document.createElement('tr');
            
            // SKU column
            const skuCell = document.createElement('td');
            skuCell.textContent = product.sku;
            tr.appendChild(skuCell);
            
            // Name column
            const nameCell = document.createElement('td');
            nameCell.textContent = product.name;
            // Add visual indicator for variants
            if (product.type === 'variante') {
                nameCell.style.paddingLeft = '2rem';
                nameCell.style.fontStyle = 'italic';
            }
            tr.appendChild(nameCell);
            
            // Stock columns (one per warehouse)
            data.warehouses.forEach(warehouse => {
                const stockCell = document.createElement('td');
                stockCell.className = 'numeric';
                const stockValue = product.stock_by_warehouse[warehouse.id] || 0;
                stockCell.textContent = stockValue;
                
                // Add visual styling for zero stock
                if (stockValue === 0) {
                    stockCell.style.color = 'var(--text-secondary)';
                    stockCell.style.opacity = '0.5';
                }
                
                tr.appendChild(stockCell);
            });
            
            stockByWarehouseTableBody.appendChild(tr);
        });
    }
    
    // Update summary stats
    stockWarehousesCount.textContent = data.summary.total_warehouses.toLocaleString();
    stockProductsCount.textContent = data.summary.total_products.toLocaleString();
    stockVariantsCount.textContent = data.summary.total_variants.toLocaleString();
    
    // Show section and ensure it's expanded
    stockByWarehouseSection.style.display = 'block';
    stockByWarehouseSection.classList.remove('collapsed');
    isStockByWarehouseCollapsed = false;
    
    // Scroll to section
    setTimeout(() => {
        stockByWarehouseSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 300);
}

// Fetch stock by warehouse
fetchStockByWarehouseBtn.addEventListener('click', async () => {
    // Show progress
    progressContainer.style.display = 'block';
    fetchStockByWarehouseBtn.disabled = true;
    hideStatus();

    try {
        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 5;
            if (progress <= 90) {
                updateProgress(progress);
            }
        }, 200);

        const response = await fetch('/api/holded/stock-by-warehouse');

        clearInterval(progressInterval);
        updateProgress(100);

        if (response.ok) {
            const result = await response.json();
            showStatus(`¡Consulta exitosa! ${result.summary.total_products + result.summary.total_variants} productos/variantes encontrados en ${result.summary.total_warehouses} almacenes`, 'success');
            
            // Render stock by warehouse
            renderStockByWarehouse(result);
            
            // Hide progress after delay
            setTimeout(() => {
                progressContainer.style.display = 'none';
            }, 1500);
            
            fetchStockByWarehouseBtn.disabled = false;
        } else {
            const error = await response.json();
            showStatus(error.detail || 'Error al obtener stock por almacén', 'error');
            fetchStockByWarehouseBtn.disabled = false;
            progressContainer.style.display = 'none';
        }
    } catch (error) {
        console.error('Fetch stock by warehouse error:', error);
        showStatus('Error de conexión. Por favor, intenta nuevamente.', 'error');
        fetchStockByWarehouseBtn.disabled = false;
        progressContainer.style.display = 'none';
    }
});

// Logo Easter Egg
const logo = document.getElementById('logo');
let clickCount = 0;
logo.addEventListener('click', () => {
    clickCount++;
    logo.style.transform = 'rotate(360deg) scale(1.1)';
    setTimeout(() => {
        logo.style.transform = '';
    }, 600);
    
    if (clickCount === 5) {
        showStatus('¡Has descubierto el easter egg! 🎉', 'success');
        clickCount = 0;
    }
});

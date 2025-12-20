// DOM Elements
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const removeBtn = document.getElementById('removeBtn');
const validateStockBtn = document.getElementById('validateStockBtn');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const statusMessage = document.getElementById('statusMessage');
const dataSection = document.getElementById('dataSection');
const tableHead = document.getElementById('tableHead');
const tableBody = document.getElementById('tableBody');
const rowCount = document.getElementById('rowCount');
const columnCount = document.getElementById('columnCount');
const clearBtn = document.getElementById('clearBtn');
const toggleTableBtn = document.getElementById('toggleTableBtn');
const dataHeaderToggle = document.getElementById('dataHeaderToggle');

// Validation section elements
const validationSection = document.getElementById('validationSection');
const toggleValidationBtn = document.getElementById('toggleValidationBtn');
const validationHeaderToggle = document.getElementById('validationHeaderToggle');
const clearValidationBtn = document.getElementById('clearValidationBtn');
const validationTableBody = document.getElementById('validationTableBody');

let selectedFile = null;
let isTableCollapsed = false;
let isValidationCollapsed = false;

// Toggle table visibility
function toggleTable() {
    isTableCollapsed = !isTableCollapsed;
    dataSection.classList.toggle('collapsed', isTableCollapsed);
}

// Add click handlers for toggle
toggleTableBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleTable();
});

dataHeaderToggle.addEventListener('click', (e) => {
    // Don't toggle if clicking on clear button
    if (!e.target.closest('.clear-btn')) {
        toggleTable();
    }
});

// Toggle validation visibility
function toggleValidation() {
    isValidationCollapsed = !isValidationCollapsed;
    validationSection.classList.toggle('collapsed', isValidationCollapsed);
}

// Add click handlers for validation toggle
toggleValidationBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleValidation();
});

validationHeaderToggle.addEventListener('click', (e) => {
    // Don't toggle if clicking on clear button
    if (!e.target.closest('.clear-btn')) {
        toggleValidation();
    }
});

// Clear validation data
clearValidationBtn.addEventListener('click', () => {
    validationSection.style.display = 'none';
    validationTableBody.innerHTML = '';
});

// File size formatter
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

// Check if value is numeric
function isNumeric(value) {
    if (typeof value === 'number') return true;
    if (typeof value === 'string') {
        // Remove spaces and check if it's a number
        const cleaned = value.trim().replace(/,/g, '.');
        return !isNaN(cleaned) && !isNaN(parseFloat(cleaned)) && cleaned !== '';
    }
    return false;
}

// Render table with data
function renderTable(columns, data) {
    // Clear existing content
    tableHead.innerHTML = '';
    tableBody.innerHTML = '';
    
    // Create header
    const headerRow = document.createElement('tr');
    columns.forEach(column => {
        const th = document.createElement('th');
        th.textContent = column;
        headerRow.appendChild(th);
    });
    tableHead.appendChild(headerRow);
    
    // Create rows
    data.forEach((row, index) => {
        const tr = document.createElement('tr');
        columns.forEach(column => {
            const td = document.createElement('td');
            const value = row[column];
            td.textContent = value;
            
            // Add numeric class if value is numeric
            if (isNumeric(value)) {
                td.classList.add('numeric');
            }
            
            tr.appendChild(td);
        });
        tableBody.appendChild(tr);
    });
    
    // Update stats
    rowCount.textContent = data.length;
    columnCount.textContent = columns.length;
    
    // Show data section and ensure it's expanded
    dataSection.style.display = 'block';
    dataSection.classList.remove('collapsed');
    isTableCollapsed = false;
    
    // Scroll to table
    setTimeout(() => {
        dataSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 300);
}

// Clear table data
clearBtn.addEventListener('click', () => {
    dataSection.style.display = 'none';
    tableHead.innerHTML = '';
    tableBody.innerHTML = '';
    rowCount.textContent = '0';
    columnCount.textContent = '0';
});

// Handle file selection
function handleFileSelect(file) {
    if (!file) return;

    // Validate file type
    if (!file.name.endsWith('.csv')) {
        showStatus('Por favor selecciona un archivo CSV válido', 'error');
        return;
    }

    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    fileInfo.style.display = 'flex';
    validateStockBtn.disabled = false;
    hideStatus();
    
    // Hide data section when new file is selected
    dataSection.style.display = 'none';
    validationSection.style.display = 'none';
}

// File input change event
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    handleFileSelect(file);
});

// Drag and drop events
uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('drag-over');
});

uploadZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    
    const file = e.dataTransfer.files[0];
    handleFileSelect(file);
});

// Remove file
removeBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    selectedFile = null;
    fileInput.value = '';
    fileInfo.style.display = 'none';
    validateStockBtn.disabled = true;
    progressContainer.style.display = 'none';
    hideStatus();
    dataSection.style.display = 'none';
    validationSection.style.display = 'none';
});

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

// Logo Easter Egg - Click animation
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

// Render validation results
function renderValidationResults(data) {
    // Update file info
    document.getElementById('valFilename').textContent = data.file_info.filename;
    document.getElementById('valCreationDate').textContent = data.file_info.creation_date;
    document.getElementById('valTotalRows').textContent = data.file_info.total_rows.toLocaleString();
    document.getElementById('valUniqueSKUs').textContent = data.file_info.unique_skus.toLocaleString();
    document.getElementById('valTotalUnitsSold').textContent = data.file_info.total_units_sold.toLocaleString();
    
    // Update summary
    document.getElementById('valFoundItems').textContent = data.summary.found_items.toLocaleString();
    document.getElementById('valMissingItems').textContent = data.summary.missing_items.toLocaleString();
    
    // Handle missing SKUs warning
    const missingSkusWarning = document.getElementById('missingSkusWarning');
    const missingSkusList = document.getElementById('missingSkusList');
    
    if (data.missing_skus.length > 0) {
        missingSkusWarning.style.display = 'block';
        missingSkusList.innerHTML = '';
        
        data.missing_skus.forEach(item => {
            const skuItem = document.createElement('div');
            skuItem.className = 'missing-sku-item';
            skuItem.innerHTML = `
                <span class="sku-code">${item.sku}</span>
                <span class="sku-name">${item.csv_name}</span>
                <span class="sold-qty">Vendidas: ${item.sold_qty}</span>
            `;
            missingSkusList.appendChild(skuItem);
        });
    } else {
        missingSkusWarning.style.display = 'none';
    }
    
    // Render validation table
    validationTableBody.innerHTML = '';
    data.validation_results.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.sku}</td>
            <td>${item.csv_name}</td>
            <td>${item.holded_name}</td>
            <td class="numeric">${item.old_stock}</td>
            <td class="numeric">${item.sold_qty}</td>
            <td class="numeric ${item.new_stock < 0 ? 'negative-stock' : ''}">${item.new_stock}</td>
        `;
        validationTableBody.appendChild(tr);
    });
    
    // Show validation section and ensure it's expanded
    validationSection.style.display = 'block';
    validationSection.classList.remove('collapsed');
    isValidationCollapsed = false;
    
    // Scroll to validation section
    setTimeout(() => {
        validationSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 300);
}

// Validate stock button handler
validateStockBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    // Show progress
    progressContainer.style.display = 'block';
    validateStockBtn.disabled = true;
    hideStatus();

    try {
        // Simulate upload progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 5;
            if (progress <= 90) {
                updateProgress(progress);
            }
        }, 150);

        const response = await fetch('/api/stock/validate', {
            method: 'POST',
            body: formData
        });

        clearInterval(progressInterval);
        updateProgress(100);

        if (response.ok) {
            const result = await response.json();
            showStatus(`¡Validación completada! ${result.summary.found_items} SKUs encontrados, ${result.summary.missing_items} no encontrados`, 
                      result.summary.missing_items > 0 ? 'warning' : 'success');
            
            // Render validation results
            renderValidationResults(result);
            
            // Hide progress after delay
            setTimeout(() => {
                progressContainer.style.display = 'none';
            }, 2000);
            
            validateStockBtn.disabled = false;
        } else {
            const error = await response.json();
            showStatus(error.detail || 'Error al validar stock', 'error');
            validateStockBtn.disabled = false;
            progressContainer.style.display = 'none';
        }
    } catch (error) {
        console.error('Validation error:', error);
        showStatus('Error de conexión. Por favor, intenta nuevamente.', 'error');
        validateStockBtn.disabled = false;
        progressContainer.style.display = 'none';
    }
});

// Holded Warehouses Section
const fetchWarehousesBtn = document.getElementById('fetchWarehousesBtn');
const holdedWarehousesSection = document.getElementById('holdedWarehousesSection');
const toggleHoldedWarehousesBtn = document.getElementById('toggleHoldedWarehousesBtn');
const holdedWarehousesHeaderToggle = document.getElementById('holdedWarehousesHeaderToggle');
const clearHoldedWarehousesBtn = document.getElementById('clearHoldedWarehousesBtn');
const warehousesTableBody = document.getElementById('warehousesTableBody');
const warehousesCount = document.getElementById('warehousesCount');

let isHoldedWarehousesCollapsed = false;

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

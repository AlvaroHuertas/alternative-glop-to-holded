// DOM Elements
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const removeBtn = document.getElementById('removeBtn');
const uploadBtn = document.getElementById('uploadBtn');
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

let selectedFile = null;
let isTableCollapsed = false;

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
    uploadBtn.disabled = false;
    hideStatus();
    
    // Hide data section when new file is selected
    dataSection.style.display = 'none';
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
    uploadBtn.disabled = true;
    progressContainer.style.display = 'none';
    hideStatus();
    dataSection.style.display = 'none';
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

// Upload file
uploadBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    // Show progress
    progressContainer.style.display = 'block';
    uploadBtn.disabled = true;
    hideStatus();

    try {
        // Simulate upload progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 10;
            if (progress <= 90) {
                updateProgress(progress);
            }
        }, 100);

        const response = await fetch('/api/upload-csv', {
            method: 'POST',
            body: formData
        });

        clearInterval(progressInterval);
        updateProgress(100);

        if (response.ok) {
            const result = await response.json();
            showStatus(`¡Archivo procesado! ${result.rows} filas cargadas`, 'success');
            
            // Render table
            renderTable(result.columns, result.data);
            
            // Hide progress after delay
            setTimeout(() => {
                progressContainer.style.display = 'none';
            }, 2000);
            
            uploadBtn.disabled = false;
        } else {
            const error = await response.json();
            showStatus(error.detail || 'Error al subir el archivo', 'error');
            uploadBtn.disabled = false;
            progressContainer.style.display = 'none';
        }
    } catch (error) {
        console.error('Upload error:', error);
        showStatus('Error de conexión. Por favor, intenta nuevamente.', 'error');
        uploadBtn.disabled = false;
        progressContainer.style.display = 'none';
    }
});

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

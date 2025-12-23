// Stock Update Simulation Script

// DOM Elements
const tabGsUri = document.getElementById('tabGsUri');
const tabFileUpload = document.getElementById('tabFileUpload');
const gsUriSection = document.getElementById('gsUriSection');
const fileUploadSection = document.getElementById('fileUploadSection');
const gsUriInput = document.getElementById('gsUriInput');
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const removeBtn = document.getElementById('removeBtn');
const simulateBtn = document.getElementById('simulateBtn');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const statusMessage = document.getElementById('statusMessage');

// Simulation section elements
const simulationSection = document.getElementById('simulationSection');
const toggleSimulationBtn = document.getElementById('toggleSimulationBtn');
const simulationHeaderToggle = document.getElementById('simulationHeaderToggle');
const clearSimulationBtn = document.getElementById('clearSimulationBtn');
const simProcessed = document.getElementById('simProcessed');
const simUpdated = document.getElementById('simUpdated');
const simErrors = document.getElementById('simErrors');
const updatesSubsection = document.getElementById('updatesSubsection');
const errorsSubsection = document.getElementById('errorsSubsection');
const updatesTableBody = document.getElementById('updatesTableBody');
const errorsTableBody = document.getElementById('errorsTableBody');

let selectedFile = null;
let currentMethod = 'gs_uri'; // 'gs_uri' or 'file_upload'
let isSimulationCollapsed = false;

// =====================
// Tab Switching
// =====================

tabGsUri.addEventListener('click', () => {
    currentMethod = 'gs_uri';
    tabGsUri.classList.add('active');
    tabFileUpload.classList.remove('active');
    gsUriSection.style.display = 'block';
    fileUploadSection.style.display = 'none';
    updateSimulateButtonState();
});

tabFileUpload.addEventListener('click', () => {
    currentMethod = 'file_upload';
    tabFileUpload.classList.add('active');
    tabGsUri.classList.remove('active');
    gsUriSection.style.display = 'none';
    fileUploadSection.style.display = 'block';
    updateSimulateButtonState();
});

// =====================
// GCS URI Input
// =====================

gsUriInput.addEventListener('input', () => {
    updateSimulateButtonState();
});

// =====================
// File Upload
// =====================

// File size formatter
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

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
    uploadZone.style.display = 'none';
    updateSimulateButtonState();
    hideStatus();
}

// File input change event
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    handleFileSelect(file);
});

// Drag and drop events
uploadZone.addEventListener('click', () => {
    fileInput.click();
});

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
    uploadZone.style.display = 'flex';
    updateSimulateButtonState();
    hideStatus();
});

// =====================
// Status & Progress
// =====================

function showStatus(message, type = 'success') {
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
    statusMessage.style.display = 'block';
}

function hideStatus() {
    statusMessage.style.display = 'none';
}

function updateProgress(percent) {
    progressFill.style.width = `${percent}%`;
    progressText.textContent = `${percent}%`;
}

function updateSimulateButtonState() {
    if (currentMethod === 'gs_uri') {
        simulateBtn.disabled = !gsUriInput.value.trim();
    } else {
        simulateBtn.disabled = !selectedFile;
    }
}

// =====================
// Simulation Section Toggle
// =====================

function toggleSimulation() {
    isSimulationCollapsed = !isSimulationCollapsed;
    simulationSection.classList.toggle('collapsed', isSimulationCollapsed);
}

toggleSimulationBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleSimulation();
});

simulationHeaderToggle.addEventListener('click', (e) => {
    if (!e.target.closest('.clear-btn')) {
        toggleSimulation();
    }
});

clearSimulationBtn.addEventListener('click', () => {
    simulationSection.style.display = 'none';
    updatesTableBody.innerHTML = '';
    errorsTableBody.innerHTML = '';
    simProcessed.textContent = '0';
    simUpdated.textContent = '0';
    simErrors.textContent = '0';
});

// =====================
// Render Simulation Results
// =====================

function renderSimulationResults(data) {
    // Update summary stats
    simProcessed.textContent = (data.processed || 0).toLocaleString();
    simUpdated.textContent = (data.updated || 0).toLocaleString();
    simErrors.textContent = (data.errors?.length || 0).toLocaleString();

    // Render updates table
    updatesTableBody.innerHTML = '';
    if (data.updates && data.updates.length > 0) {
        updatesSubsection.style.display = 'block';
        data.updates.forEach(update => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${update.sku || '-'}</td>
                <td>${update.product || '-'}</td>
                <td>${update.warehouse || '-'}</td>
                <td class="numeric">${update.units_sold || 0}</td>
                <td class="numeric">${update.current_stock || 0}</td>
                <td class="numeric ${update.new_stock < 0 ? 'negative-stock' : ''}">${update.new_stock || 0}</td>
            `;
            updatesTableBody.appendChild(tr);
        });
    } else {
        updatesSubsection.style.display = 'none';
    }

    // Render errors table
    errorsTableBody.innerHTML = '';
    if (data.errors && data.errors.length > 0) {
        errorsSubsection.style.display = 'block';
        data.errors.forEach(error => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="numeric">${error.row !== undefined ? error.row : '-'}</td>
                <td>${error.sku || '-'}</td>
                <td>${error.product || '-'}</td>
                <td>${error.terminal || '-'}</td>
                <td class="numeric">${error.units || '-'}</td>
                <td class="error-text">${error.error || '-'}</td>
            `;
            errorsTableBody.appendChild(tr);
        });
    } else {
        errorsSubsection.style.display = 'none';
    }

    // Show simulation section and ensure it's expanded
    simulationSection.style.display = 'block';
    simulationSection.classList.remove('collapsed');
    isSimulationCollapsed = false;

    // Scroll to simulation section
    setTimeout(() => {
        simulationSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 300);
}

// =====================
// Simulate Button Handler
// =====================

simulateBtn.addEventListener('click', async () => {
    let gsUri = '';

    // Show progress
    progressContainer.style.display = 'block';
    simulateBtn.disabled = true;
    hideStatus();

    try {
        // If file upload method, first upload the file to GCS
        if (currentMethod === 'file_upload') {
            if (!selectedFile) return;

            showStatus('Subiendo archivo a Cloud Storage...', 'info');
            
            const formData = new FormData();
            formData.append('file', selectedFile);

            let progress = 0;
            const uploadProgressInterval = setInterval(() => {
                progress += 3;
                if (progress <= 40) {
                    updateProgress(progress);
                }
            }, 100);

            const uploadResponse = await fetch('/api/gcs/upload', {
                method: 'POST',
                body: formData
            });

            clearInterval(uploadProgressInterval);

            if (!uploadResponse.ok) {
                const error = await uploadResponse.json();
                throw new Error(error.detail || 'Error al subir archivo a GCS');
            }

            const uploadResult = await uploadResponse.json();
            if (uploadResult.status !== 'success') {
                throw new Error(uploadResult.message || 'Error al subir archivo');
            }

            // Build the gs_uri from the uploaded file info
            gsUri = `gs://${uploadResult.file.bucket}/${uploadResult.file.name}`;
            updateProgress(50);
        } else {
            // GCS URI method - build full URI
            const inputValue = gsUriInput.value.trim();
            gsUri = inputValue.startsWith('gs://') ? inputValue : `gs://${inputValue}`;
        }

        showStatus('Ejecutando simulación...', 'info');

        // Simulate progress for API call
        let progress = currentMethod === 'file_upload' ? 50 : 0;
        const progressInterval = setInterval(() => {
            progress += 5;
            if (progress <= 90) {
                updateProgress(progress);
            }
        }, 200);

        // Call the update-from-gcs endpoint with dry_run=true
        const response = await fetch('/api/holded/stock/update-from-gcs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                gs_uri: gsUri,
                dry_run: true
            })
        });

        clearInterval(progressInterval);
        updateProgress(100);

        if (response.ok) {
            const result = await response.json();
            
            const errorCount = result.errors?.length || 0;
            const updateCount = result.updated || 0;
            
            if (errorCount > 0 && updateCount > 0) {
                showStatus(`Simulación completada: ${updateCount} actualizaciones, ${errorCount} errores`, 'warning');
            } else if (errorCount > 0) {
                showStatus(`Simulación completada con ${errorCount} errores`, 'warning');
            } else {
                showStatus(`¡Simulación exitosa! ${updateCount} actualizaciones simuladas`, 'success');
            }
            
            // Render simulation results
            renderSimulationResults(result);
            
            // Hide progress after delay
            setTimeout(() => {
                progressContainer.style.display = 'none';
            }, 2000);
            
            simulateBtn.disabled = false;
        } else {
            const error = await response.json();
            showStatus(error.detail || 'Error al ejecutar simulación', 'error');
            simulateBtn.disabled = false;
            progressContainer.style.display = 'none';
        }
    } catch (error) {
        console.error('Simulation error:', error);
        showStatus(error.message || 'Error de conexión. Por favor, intenta nuevamente.', 'error');
        simulateBtn.disabled = false;
        progressContainer.style.display = 'none';
    }

    updateSimulateButtonState();
});

// =====================
// Logo Easter Egg
// =====================

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

// Initialize
updateSimulateButtonState();

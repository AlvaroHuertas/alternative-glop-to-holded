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

// Apply button and real update section elements
const applySection = document.getElementById('applySection');
const applyBtn = document.getElementById('applyBtn');
const realUpdateSection = document.getElementById('realUpdateSection');
const toggleRealUpdateBtn = document.getElementById('toggleRealUpdateBtn');
const realUpdateHeaderToggle = document.getElementById('realUpdateHeaderToggle');
const clearRealUpdateBtn = document.getElementById('clearRealUpdateBtn');
const realProcessed = document.getElementById('realProcessed');
const realUpdated = document.getElementById('realUpdated');
const realErrors = document.getElementById('realErrors');
const realUpdatesSubsection = document.getElementById('realUpdatesSubsection');
const realErrorsSubsection = document.getElementById('realErrorsSubsection');
const realUpdatesTableBody = document.getElementById('realUpdatesTableBody');
const realErrorsTableBody = document.getElementById('realErrorsTableBody');

let selectedFile = null;
let currentMethod = 'gs_uri'; // 'gs_uri' or 'file_upload'
let isSimulationCollapsed = false;
let isRealUpdateCollapsed = false;
let lastSimulatedGsUri = ''; // Store the GS URI from last simulation
let currentUpdatesData = []; // Store updates data for fullscreen view

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
    applySection.style.display = 'none';
    updatesTableBody.innerHTML = '';
    errorsTableBody.innerHTML = '';
    simProcessed.textContent = '0';
    simUpdated.textContent = '0';
    simErrors.textContent = '0';
    lastSimulatedGsUri = '';
});

// =====================
// Render Simulation Results
// =====================

function renderSimulationResults(data) {
    // Update summary stats
    simProcessed.textContent = (data.processed || 0).toLocaleString();
    simUpdated.textContent = (data.updated || 0).toLocaleString();
    simErrors.textContent = (data.errors?.length || 0).toLocaleString();

    // Store updates data for fullscreen view
    currentUpdatesData = data.updates || [];

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

    // Show apply button if there are successful updates
    if (data.updates && data.updates.length > 0) {
        applySection.style.display = 'block';
    } else {
        applySection.style.display = 'none';
    }

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
            
            // Store GS URI for apply button
            lastSimulatedGsUri = gsUri;
            
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
// Real Update Section Toggle
// =====================

function toggleRealUpdate() {
    isRealUpdateCollapsed = !isRealUpdateCollapsed;
    realUpdateSection.classList.toggle('collapsed', isRealUpdateCollapsed);
}

toggleRealUpdateBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleRealUpdate();
});

realUpdateHeaderToggle.addEventListener('click', (e) => {
    if (!e.target.closest('.clear-btn')) {
        toggleRealUpdate();
    }
});

clearRealUpdateBtn.addEventListener('click', () => {
    realUpdateSection.style.display = 'none';
    realUpdatesTableBody.innerHTML = '';
    realErrorsTableBody.innerHTML = '';
    realProcessed.textContent = '0';
    realUpdated.textContent = '0';
    realErrors.textContent = '0';
});

// =====================
// Render Real Update Results
// =====================

function renderRealUpdateResults(data) {
    // Update summary stats
    realProcessed.textContent = (data.processed || 0).toLocaleString();
    realUpdated.textContent = (data.updated || 0).toLocaleString();
    realErrors.textContent = (data.errors?.length || 0).toLocaleString();

    // Render updates table with adjustment column
    realUpdatesTableBody.innerHTML = '';
    if (data.updates && data.updates.length > 0) {
        realUpdatesSubsection.style.display = 'block';
        data.updates.forEach(update => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${update.sku || '-'}</td>
                <td>${update.product || '-'}</td>
                <td>${update.warehouse || '-'}</td>
                <td class="numeric">${update.current_stock || 0}</td>
                <td class="numeric adjustment-cell">${update.adjustment || 0}</td>
                <td class="numeric ${update.new_stock < 0 ? 'negative-stock' : ''}">${update.new_stock || 0}</td>
            `;
            realUpdatesTableBody.appendChild(tr);
        });
    } else {
        realUpdatesSubsection.style.display = 'none';
    }

    // Render errors table
    realErrorsTableBody.innerHTML = '';
    if (data.errors && data.errors.length > 0) {
        realErrorsSubsection.style.display = 'block';
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
            realErrorsTableBody.appendChild(tr);
        });
    } else {
        realErrorsSubsection.style.display = 'none';
    }

    // Show real update section and ensure it's expanded
    realUpdateSection.style.display = 'block';
    realUpdateSection.classList.remove('collapsed');
    isRealUpdateCollapsed = false;

    // Scroll to real update section
    setTimeout(() => {
        realUpdateSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 300);
}

// =====================
// Apply Button Handler
// =====================

applyBtn.addEventListener('click', async () => {
    if (!lastSimulatedGsUri) {
        showStatus('No hay simulación previa. Ejecuta primero una simulación.', 'error');
        return;
    }

    // Confirmation dialog
    const confirmed = confirm(
        '⚠️ ATENCIÓN: Esta acción modificará la base de datos de Holded.\n\n' +
        'Los cambios NO se pueden deshacer automáticamente.\n\n' +
        '¿Estás seguro de que deseas aplicar los cambios?'
    );

    if (!confirmed) {
        return;
    }

    // Show progress
    progressContainer.style.display = 'block';
    applyBtn.disabled = true;
    simulateBtn.disabled = true;
    hideStatus();

    try {
        showStatus('Aplicando cambios en Holded...', 'info');

        // Simulate progress for API call
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 3;
            if (progress <= 90) {
                updateProgress(progress);
            }
        }, 200);

        // Call the update-from-gcs endpoint with dry_run=false
        const response = await fetch('/api/holded/stock/update-from-gcs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                gs_uri: lastSimulatedGsUri,
                dry_run: false
            })
        });

        clearInterval(progressInterval);
        updateProgress(100);

        if (response.ok) {
            const result = await response.json();
            
            const errorCount = result.errors?.length || 0;
            const updateCount = result.updated || 0;
            
            if (errorCount > 0 && updateCount > 0) {
                showStatus(`Actualización completada: ${updateCount} productos actualizados, ${errorCount} errores`, 'warning');
            } else if (errorCount > 0) {
                showStatus(`Actualización completada con ${errorCount} errores`, 'warning');
            } else {
                showStatus(`¡Actualización exitosa! ${updateCount} productos actualizados en Holded`, 'success');
            }
            
            // Hide apply section after successful apply
            applySection.style.display = 'none';
            
            // Render real update results
            renderRealUpdateResults(result);
            
            // Hide progress after delay
            setTimeout(() => {
                progressContainer.style.display = 'none';
            }, 2000);
            
            applyBtn.disabled = false;
            simulateBtn.disabled = false;
        } else {
            const error = await response.json();
            showStatus(error.detail || 'Error al aplicar cambios', 'error');
            applyBtn.disabled = false;
            simulateBtn.disabled = false;
            progressContainer.style.display = 'none';
        }
    } catch (error) {
        console.error('Apply error:', error);
        showStatus(error.message || 'Error de conexión. Por favor, intenta nuevamente.', 'error');
        applyBtn.disabled = false;
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

// =====================
// Fullscreen Modal
// =====================

const fullscreenModal = document.getElementById('fullscreenModal');
const fullscreenUpdatesBtn = document.getElementById('fullscreenUpdatesBtn');
const closeFullscreenBtn = document.getElementById('closeFullscreenBtn');
const fullscreenUpdatesTableBody = document.getElementById('fullscreenUpdatesTableBody');

function openFullscreenModal() {
    // Copy current updates data to fullscreen table
    fullscreenUpdatesTableBody.innerHTML = '';
    currentUpdatesData.forEach(update => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${update.sku || '-'}</td>
            <td>${update.product || '-'}</td>
            <td>${update.warehouse || '-'}</td>
            <td class="numeric">${update.units_sold || 0}</td>
            <td class="numeric">${update.current_stock || 0}</td>
            <td class="numeric ${update.new_stock < 0 ? 'negative-stock' : ''}">${update.new_stock || 0}</td>
        `;
        fullscreenUpdatesTableBody.appendChild(tr);
    });
    
    fullscreenModal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeFullscreenModal() {
    fullscreenModal.classList.remove('active');
    document.body.style.overflow = '';
}

fullscreenUpdatesBtn.addEventListener('click', openFullscreenModal);
closeFullscreenBtn.addEventListener('click', closeFullscreenModal);

// Close modal with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && fullscreenModal.classList.contains('active')) {
        closeFullscreenModal();
    }
});

// Close modal when clicking outside
fullscreenModal.addEventListener('click', (e) => {
    if (e.target === fullscreenModal) {
        closeFullscreenModal();
    }
});

// Initialize
updateSimulateButtonState();


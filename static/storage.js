// Cloud Storage Management Script

let selectedFile = null;
let filesData = [];

// DOM Elements
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const removeBtn = document.getElementById('removeBtn');
const uploadBtn = document.getElementById('uploadBtn');
const refreshBtn = document.getElementById('refreshBtn');
const searchInput = document.getElementById('searchInput');
const prefixFilter = document.getElementById('prefixFilter');
const filesTableBody = document.getElementById('filesTableBody');
const statusMessage = document.getElementById('statusMessage');
const gcsStatus = document.getElementById('gcsStatus');
const statusText = document.getElementById('statusText');
const storageStats = document.getElementById('storageStats');
const filesSection = document.getElementById('filesSection');
const fileModal = document.getElementById('fileModal');
const modalClose = document.getElementById('modalClose');
const modalTitle = document.getElementById('modalTitle');
const modalBody = document.getElementById('modalBody');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkGCSHealth();
    loadFiles();
    setupEventListeners();
});

function setupEventListeners() {
    // Upload zone interactions
    uploadZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });
    
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect({ target: { files } });
        }
    });
    
    removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        clearFileSelection();
    });
    
    uploadBtn.addEventListener('click', uploadFile);
    refreshBtn.addEventListener('click', loadFiles);
    searchInput.addEventListener('input', filterFiles);
    prefixFilter.addEventListener('input', () => loadFiles());
    modalClose.addEventListener('click', () => fileModal.style.display = 'none');
    
    // Close modal when clicking outside
    fileModal.addEventListener('click', (e) => {
        if (e.target === fileModal) {
            fileModal.style.display = 'none';
        }
    });
}

async function checkGCSHealth() {
    try {
        const response = await fetch('/api/gcs/health');
        const data = await response.json();
        
        const statusDot = gcsStatus.querySelector('.status-dot');
        
        if (data.connection_test.status === 'success') {
            statusDot.className = 'status-dot success';
            statusText.textContent = `✓ Conectado: ${data.bucket_name}`;
        } else {
            statusDot.className = 'status-dot error';
            statusText.textContent = `✗ ${data.connection_test.message}`;
            showMessage(data.connection_test.message, 'error');
        }
    } catch (error) {
        const statusDot = gcsStatus.querySelector('.status-dot');
        statusDot.className = 'status-dot error';
        statusText.textContent = '✗ Error de conexión';
        showMessage('Error al verificar conexión con GCS', 'error');
    }
}

async function loadFiles() {
    try {
        const prefix = prefixFilter.value.trim();
        const url = prefix ? `/api/gcs/files?prefix=${encodeURIComponent(prefix)}` : '/api/gcs/files';
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.status === 'success') {
            filesData = data.files;
            renderFiles(filesData);
            updateStats(data);
            storageStats.style.display = 'grid';
            filesSection.style.display = 'block';
        } else {
            throw new Error(data.message || 'Error al cargar archivos');
        }
    } catch (error) {
        showMessage(`Error al cargar archivos: ${error.message}`, 'error');
    }
}

function updateStats(data) {
    document.getElementById('totalFiles').textContent = data.count;
    document.getElementById('totalSize').textContent = `${data.total_size_mb} MB`;
}

function renderFiles(files) {
    filesTableBody.innerHTML = '';
    
    if (files.length === 0) {
        filesTableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 2rem;">No se encontraron archivos</td></tr>';
        return;
    }
    
    files.forEach(file => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <svg style="width: 1.2rem; height: 1.2rem; color: #6366f1;" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span>${file.name}</span>
                </div>
            </td>
            <td>${file.size_mb} MB</td>
            <td><code style="font-size: 0.75rem;">${file.content_type || 'N/A'}</code></td>
            <td>${formatDate(file.created)}</td>
            <td>${formatDate(file.updated)}</td>
            <td>
                <div style="display: flex; gap: 0.5rem;">
                    <button class="action-btn" onclick="viewFileDetails('${file.name}')" title="Ver detalles">
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M15 12C15 13.6569 13.6569 15 12 15C10.3431 15 9 13.6569 9 12C9 10.3431 10.3431 9 12 9C13.6569 9 15 10.3431 15 12Z" stroke="currentColor" stroke-width="2"/>
                            <path d="M2 12C2 12 5 5 12 5C19 5 22 12 22 12C22 12 19 19 12 19C5 19 2 12 2 12Z" stroke="currentColor" stroke-width="2"/>
                        </svg>
                    </button>
                    <button class="action-btn" onclick="downloadFile('${file.name}')" title="Descargar">
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15M7 10L12 15M12 15L17 10M12 15V3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                    <button class="action-btn delete-btn" onclick="deleteFile('${file.name}')" title="Eliminar">
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M3 6H5H21M19 6V20C19 20.5304 18.7893 21.0391 18.4142 21.4142C18.0391 21.7893 17.5304 22 17 22H7C6.46957 22 5.96086 21.7893 5.58579 21.4142C5.21071 21.0391 5 20.5304 5 20V6M8 6V4C8 3.46957 8.21071 2.96086 8.58579 2.58579C8.96086 2.21071 9.46957 2 10 2H14C14.5304 2 15.0391 2.21071 15.4142 2.58579C15.7893 2.96086 16 3.46957 16 4V6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                </div>
            </td>
        `;
        filesTableBody.appendChild(row);
    });
}

function filterFiles() {
    const searchTerm = searchInput.value.toLowerCase();
    const filtered = filesData.filter(file => 
        file.name.toLowerCase().includes(searchTerm)
    );
    renderFiles(filtered);
}

function handleFileSelect(event) {
    const files = event.target.files;
    if (files.length > 0) {
        selectedFile = files[0];
        displayFileInfo(selectedFile);
        uploadBtn.disabled = false;
    }
}

function displayFileInfo(file) {
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    fileInfo.style.display = 'flex';
    uploadZone.style.display = 'none';
}

function clearFileSelection() {
    selectedFile = null;
    fileInput.value = '';
    fileInfo.style.display = 'none';
    uploadZone.style.display = 'flex';
    uploadBtn.disabled = true;
}

async function uploadFile() {
    if (!selectedFile) return;
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<span class="btn-text">Subiendo...</span>';
        
        const response = await fetch('/api/gcs/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showMessage(`✓ ${data.message}`, 'success');
            clearFileSelection();
            loadFiles();
        } else {
            throw new Error(data.message || 'Error al subir archivo');
        }
    } catch (error) {
        showMessage(`✗ Error: ${error.message}`, 'error');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = `
            <span class="btn-text">Subir a Cloud Storage</span>
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M7 16C5.89543 16 5 15.1046 5 14C5 12.8954 5.89543 12 7 12C7 9.23858 9.23858 7 12 7C14.419 7 16.4367 8.71776 16.9 11M17 16C18.1046 16 19 15.1046 19 14C19 12.8954 18.1046 12 17 12C17 9.23858 14.7614 7 12 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 13V21M12 13L9 16M12 13L15 16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        `;
    }
}

async function downloadFile(filePath) {
    try {
        const response = await fetch(`/api/gcs/download/${encodeURIComponent(filePath)}`);
        if (!response.ok) throw new Error('Error al descargar archivo');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filePath.split('/').pop();
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showMessage('✓ Archivo descargado', 'success');
    } catch (error) {
        showMessage(`✗ Error al descargar: ${error.message}`, 'error');
    }
}

async function deleteFile(filePath) {
    if (!confirm(`¿Estás seguro de que quieres eliminar "${filePath}"?`)) return;
    
    try {
        const response = await fetch(`/api/gcs/delete/${encodeURIComponent(filePath)}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showMessage(`✓ ${data.message}`, 'success');
            loadFiles();
        } else {
            throw new Error(data.message || 'Error al eliminar archivo');
        }
    } catch (error) {
        showMessage(`✗ Error: ${error.message}`, 'error');
    }
}

async function viewFileDetails(filePath) {
    try {
        const response = await fetch(`/api/gcs/metadata/${encodeURIComponent(filePath)}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            const file = data.file;
            modalTitle.textContent = 'Detalles del Archivo';
            modalBody.innerHTML = `
                <div class="metadata-grid">
                    <div class="metadata-item">
                        <strong>Nombre:</strong>
                        <span>${file.name}</span>
                    </div>
                    <div class="metadata-item">
                        <strong>Bucket:</strong>
                        <code>${file.bucket}</code>
                    </div>
                    <div class="metadata-item">
                        <strong>Tamaño:</strong>
                        <span>${file.size.mb} MB (${file.size.bytes} bytes)</span>
                    </div>
                    <div class="metadata-item">
                        <strong>Tipo de Contenido:</strong>
                        <code>${file.content_type || 'N/A'}</code>
                    </div>
                    <div class="metadata-item">
                        <strong>Creado:</strong>
                        <span>${formatDate(file.dates.created)}</span>
                    </div>
                    <div class="metadata-item">
                        <strong>Modificado:</strong>
                        <span>${formatDate(file.dates.updated)}</span>
                    </div>
                    <div class="metadata-item">
                        <strong>MD5 Hash:</strong>
                        <code style="font-size: 0.75rem; word-break: break-all;">${file.checksums.md5_hash || 'N/A'}</code>
                    </div>
                    <div class="metadata-item">
                        <strong>CRC32C:</strong>
                        <code>${file.checksums.crc32c || 'N/A'}</code>
                    </div>
                    <div class="metadata-item">
                        <strong>Storage Class:</strong>
                        <span>${file.storage_class || 'N/A'}</span>
                    </div>
                    <div class="metadata-item">
                        <strong>Generation:</strong>
                        <span>${file.generation || 'N/A'}</span>
                    </div>
                </div>
            `;
            fileModal.style.display = 'flex';
        }
    } catch (error) {
        showMessage(`✗ Error al obtener detalles: ${error.message}`, 'error');
    }
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function showMessage(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
    statusMessage.style.display = 'block';
    
    setTimeout(() => {
        statusMessage.style.display = 'none';
    }, 5000);
}

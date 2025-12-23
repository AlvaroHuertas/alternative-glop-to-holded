
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from app.api.routes import holded, storage, csv, health

app = FastAPI(
    title="Alternative Glop to Holded API",
    description="""
## API de integración con Holded

Esta API proporciona endpoints para:

* 🔄 **Validación de Stock**: Procesar archivos CSV y validar contra el inventario de Holded
* 📦 **Gestión de Almacenes**: Consultar almacenes y stock distribuido por ubicación
* 📁 **Procesamiento de Archivos**: Subir y procesar archivos CSV
* ☁️ **Cloud Storage**: Gestión de archivos en Google Cloud Storage (subida, descarga, listado)
* 🏥 **Health Checks**: Verificar el estado de la API y la conexión con Holded/GCS

### Configuración

Para usar esta API, necesitas configurar las siguientes variables de entorno:
- `HOLDED_API_KEY`: Tu clave de API de Holded
- `HOLDED_BASE_URL`: URL base de la API de Holded (opcional, por defecto usa la URL de productos)
- `GCS_CREDENTIALS_BASE64`: Credenciales de servicio de Google Cloud (JSON codificado en base64)

### Autenticación e Integraciones

La API utiliza las credenciales configuradas en las variables de entorno para comunicarse con servicios externos (Holded, GCS).
Puedes verificar la configuración usando los endpoints `/api/holded/health` y `/api/gcs/health`.
    """,
    version="1.0.0",
    contact={
        "name": "Soporte API",
        "email": "soporte@example.com",
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_tags=[
        {
            "name": "Sistema",
            "description": "Endpoints del sistema y health checks"
        },
        {
            "name": "Holded",
            "description": "Endpoints de integración con Holded API"
        },
        {
            "name": "Archivos",
            "description": "Procesamiento y validación de archivos CSV"
        },
        {
            "name": "Cloud Storage",
            "description": "Gestión de archivos en Google Cloud Storage"
        }
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
# static dir is one level up from app (project root / static)
static_dir = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include Routers
app.include_router(health.router, prefix="/health", tags=["Sistema"])
app.include_router(holded.router, prefix="/api/holded", tags=["Holded"])
app.include_router(storage.router, prefix="/api/gcs", tags=["Cloud Storage"])
app.include_router(csv.router, prefix="/api", tags=["Archivos"])

@app.get("/", tags=["Sistema"], summary="Página Principal")
async def read_root():
    """Serve la página principal de la interfaz web"""
    return FileResponse(static_dir / "index.html")

@app.get("/storage", tags=["Sistema"], summary="Gestión de Cloud Storage")
async def storage_page():
    """Serve la página de gestión de Cloud Storage"""
    return FileResponse(static_dir / "storage.html")

@app.get("/holded", tags=["Sistema"], summary="Consultas Holded")
async def holded_page():
    """Serve la página de consultas a Holded"""
    return FileResponse(static_dir / "holded.html")


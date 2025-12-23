from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
from pathlib import Path
import pandas as pd
import io
from dotenv import load_dotenv
import httpx
import base64
import json
import tempfile
from google.cloud import storage
from typing import Optional
from datetime import datetime


class StockUpdateRequest(BaseModel):
    """Request model for updating product stock"""
    sku: str = Field(..., description="SKU del producto a actualizar")
    warehouse_id: str = Field(..., description="ID del almacén donde actualizar el stock")
    stock_adjustment: float = Field(..., description="Ajuste de stock: positivo para añadir, negativo para restar (ej: +10, -5)")
    description: str = Field(default="", description="Descripción del ajuste de stock (ej: 'Ajuste de stock', 'VENTAS 19 y 20 DIC')")
    dry_run: bool = Field(default=False, description="Si es True, simula la petición sin ejecutarla")

# Load environment variables (try .env.local first, then .env)
load_dotenv(".env.local")
load_dotenv()

# Holded configuration
HOLDED_API_KEY = os.getenv("HOLDED_API_KEY", "")
HOLDED_BASE_URL = os.getenv("HOLDED_BASE_URL", "https://api.holded.com/api/invoicing/v1/products")

# Google Cloud Storage configuration
GCS_CREDENTIALS_BASE64 = os.getenv("GCS_CREDENTIALS_BASE64", "")
GCS_BUCKET_NAME = "alternativecbd-glop-reports"

# Initialize GCS client
def get_gcs_client():
    """Initialize and return a Google Cloud Storage client using base64-encoded credentials"""
    if not GCS_CREDENTIALS_BASE64:
        raise HTTPException(status_code=400, detail="GCS credentials not configured")
    
    try:
        # Decode base64 credentials
        credentials_json = base64.b64decode(GCS_CREDENTIALS_BASE64).decode('utf-8')
        credentials_dict = json.loads(credentials_json)
        
        # Create a temporary file for credentials
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(credentials_dict, temp_file)
            temp_file_path = temp_file.name
        
        # Initialize client with credentials
        client = storage.Client.from_service_account_json(temp_file_path)
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        return client
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing GCS client: {str(e)}")


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
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Create uploads directory if it doesn't exist
uploads_dir = Path(__file__).parent / "uploads"
uploads_dir.mkdir(exist_ok=True)

@app.get("/", tags=["Sistema"], summary="Página Principal")
async def read_root():
    """Serve la página principal de la interfaz web"""
    return FileResponse(static_dir / "index.html")

@app.get("/storage", tags=["Sistema"], summary="Gestión de Cloud Storage")
async def storage_page():
    """Serve la página de gestión de Cloud Storage"""
    return FileResponse(static_dir / "storage.html")

@app.get("/health", tags=["Sistema"], summary="Health Check")
async def health():
    """Verifica que la API esté funcionando correctamente"""
    return {"status": "ok"}

@app.get("/api/holded/health", tags=["Holded"], summary="Verificar Configuración de Holded")
async def holded_health():
    """
    Verifica la configuración y conectividad con Holded API.
    
    **Retorna:**
    - Estado de configuración (si la API key está configurada)
    - Últimos 4 caracteres de la API key (para verificación)
    - URL base configurada
    - Resultado del test de conexión
    - Cantidad de productos (si la conexión es exitosa)
    """
    # Check if API key is configured
    api_key_configured = bool(HOLDED_API_KEY)
    
    # Get last 4 characters of API key (or empty if not set)
    api_key_suffix = HOLDED_API_KEY[-4:] if len(HOLDED_API_KEY) >= 4 else ""
    
    # Prepare response
    response = {
        "configured": api_key_configured,
        "api_key_suffix": f"...{api_key_suffix}" if api_key_suffix else "NO CONFIGURADA",
        "base_url": HOLDED_BASE_URL,
        "connection_test": {
            "status": "not_tested",
            "message": ""
        }
    }
    
    # Test connection to Holded API if configured
    if api_key_configured:
        try:
            async with httpx.AsyncClient() as client:
                # Make a simple GET request to test the connection
                headers = {
                    "key": HOLDED_API_KEY,
                    "Accept": "application/json"
                }
                test_response = await client.get(HOLDED_BASE_URL, headers=headers, timeout=10.0)
                
                if test_response.status_code == 200:
                    response["connection_test"]["status"] = "success"
                    response["connection_test"]["message"] = "Conexión exitosa con Holded API"
                    # Count products if response is successful
                    try:
                        data = test_response.json()
                        if isinstance(data, list):
                            response["connection_test"]["products_count"] = len(data)
                    except:
                        pass
                elif test_response.status_code == 401:
                    response["connection_test"]["status"] = "error"
                    response["connection_test"]["message"] = "API key inválida o sin permisos"
                else:
                    response["connection_test"]["status"] = "error"
                    response["connection_test"]["message"] = f"Error HTTP {test_response.status_code}"
        
        except httpx.TimeoutException:
            response["connection_test"]["status"] = "error"
            response["connection_test"]["message"] = "Timeout al conectar con Holded API"
        except Exception as e:
            response["connection_test"]["status"] = "error"
            response["connection_test"]["message"] = f"Error: {str(e)}"
    else:
        response["connection_test"]["status"] = "not_configured"
        response["connection_test"]["message"] = "API key no configurada"
    
    return response


@app.get("/api/holded/warehouses", tags=["Holded"], summary="Listar Almacenes")
async def get_holded_warehouses():
    """
    Obtiene la lista de almacenes desde Holded API.
    
    **Retorna:**
    - Lista de almacenes con sus detalles (ID, nombre, etc.)
    - Contador total de almacenes
    
    **Errores posibles:**
    - 400: API key no configurada
    - 401: API key inválida
    - 504: Timeout de conexión
    """
    # Check if API key is configured
    if not HOLDED_API_KEY:
        raise HTTPException(status_code=400, detail="API key de Holded no configurada")
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "key": HOLDED_API_KEY,
                "accept": "application/json"
            }
            
            warehouses_url = "https://api.holded.com/api/invoicing/v1/warehouses"
            response = await client.get(warehouses_url, headers=headers, timeout=30.0)
            
            if response.status_code == 200:
                warehouses = response.json()
                return {
                    "status": "success",
                    "count": len(warehouses) if isinstance(warehouses, list) else 0,
                    "warehouses": warehouses
                }
            elif response.status_code == 401:
                raise HTTPException(status_code=401, detail="API key inválida o sin permisos")
            else:
                raise HTTPException(
                    status_code=502,
                    detail=f"Error al obtener almacenes de Holded: HTTP {response.status_code}"
                )
    
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout al conectar con Holded API")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/api/upload-csv", tags=["Archivos"], summary="Subir y Procesar CSV")
async def upload_csv(file: UploadFile = File(...)):
    """
    Sube y procesa un archivo CSV.
    
    **Parámetros:**
    - `file`: Archivo CSV a procesar (delimitador: punto y coma)
    
    **Retorna:**
    - Información del archivo (nombre, tamaño)
    - Número de filas y columnas
    - Datos procesados en formato JSON
    
    **Errores posibles:**
    - 400: El archivo no es CSV
    - 500: Error al procesar el archivo
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="El archivo debe ser CSV")
    
    try:
        # Read file content
        contents = await file.read()
        
        # Save file
        file_path = uploads_dir / file.filename
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Parse CSV with pandas (semicolon delimiter, handle encoding)
        try:
            # Try UTF-8 first
            df = pd.read_csv(io.BytesIO(contents), sep=';', encoding='utf-8')
        except UnicodeDecodeError:
            # Fallback to latin1 if UTF-8 fails
            df = pd.read_csv(io.BytesIO(contents), sep=';', encoding='latin1')
        
        # Replace NaN with empty strings for better JSON serialization
        df = df.fillna('')
        
        # Convert to list of dictionaries
        data = df.to_dict('records')
        columns = df.columns.tolist()
        
        return {
            "message": "Archivo procesado exitosamente",
            "filename": file.filename,
            "size": len(contents),
            "rows": len(data),
            "columns": columns,
            "data": data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el archivo: {str(e)}")


@app.post("/api/stock/validate", tags=["Archivos"], summary="Validar Stock contra Holded")
async def validate_stock(file: UploadFile = File(...)):
    """
    Valida stock contra Holded API.
    
    Procesa un archivo CSV con datos de ventas y los compara contra el inventario actual de Holded.
    
    **Parámetros:**
    - `file`: Archivo CSV con columnas 'C.BARRAS ARTICULO' y 'UNIDADES'
    
    **Retorna:**
    - Información del archivo procesado
    - Estadísticas de productos en Holded
    - Resultados de validación (SKUs encontrados y faltantes)
    - Cálculo de stock nuevo vs antiguo
    - Resumen de unidades vendidas
    
    **Errores posibles:**
    - 400: API key no configurada o archivo inválido
    - 502: Error al comunicarse con Holded
    - 500: Error de procesamiento
    """
    import csv
    import datetime
    from collections import defaultdict
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="El archivo debe ser CSV")
    
    try:
        # Read file content
        contents = await file.read()
        
        # Save file temporarily
        file_path = uploads_dir / file.filename
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Get file creation date
        try:
            stat = os.stat(file_path)
            if hasattr(stat, 'st_birthtime'):
                creation_time = stat.st_birthtime
            else:
                creation_time = stat.st_ctime
            creation_date_str = datetime.datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            creation_date_str = "Desconocida"
        
        # Step 1: Fetch products from Holded API
        if not HOLDED_API_KEY:
            raise HTTPException(status_code=400, detail="API key de Holded no configurada")
        
        headers = {
            "key": HOLDED_API_KEY,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            holded_response = await client.get(HOLDED_BASE_URL, headers=headers, timeout=30.0)
            
            if holded_response.status_code != 200:
                raise HTTPException(
                    status_code=502, 
                    detail=f"Error al obtener productos de Holded: HTTP {holded_response.status_code}"
                )
            
            products = holded_response.json()
        
        # Map products by SKU
        holded_map = {}
        count_products = 0
        count_variants = 0
        
        for p in products:
            # Check main product SKU
            if p.get('sku'):
                holded_map[p['sku']] = {
                    'id': p['id'],
                    'name': p['name'],
                    'stock': p.get('stock', 0),
                    'kind': 'product'
                }
                count_products += 1
            
            # Check variants
            if 'variants' in p and isinstance(p['variants'], list):
                for v in p['variants']:
                    if v.get('sku'):
                        holded_map[v['sku']] = {
                            'id': v['id'],
                            'name': f"{p['name']} ({v.get('sku')})",
                            'stock': v.get('stock', 0),
                            'kind': 'variant'
                        }
                        count_variants += 1
        
        # Step 2: Process CSV file
        sales_data = {}  # sku -> {units: float, name: str}
        
        with open(file_path, 'r', encoding='latin-1', errors='replace') as f:
            # Detect delimiter
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            try:
                dialect = sniffer.sniff(sample)
            except:
                # Default to semicolon if detection fails
                dialect = csv.excel()
                dialect.delimiter = ';'
            
            reader = csv.DictReader(f, dialect=dialect)
            # Normalize field names
            field_names = [f.strip() for f in reader.fieldnames]
            reader.fieldnames = field_names
            
            # Identify the 'ARTICULO' column name
            articulo_col = next((col for col in field_names if 'ART' in col.upper() and 'BARRAS' not in col.upper()), 'ARTICULO')
            
            rows = list(reader)
            total_rows = len(rows)
            
            for row in rows:
                sku = row.get('C.BARRAS ARTICULO')
                units_str = row.get('UNIDADES', '0')
                name_csv = row.get(articulo_col, 'Desconocido')
                
                if not sku:
                    continue
                
                try:
                    units = float(units_str.replace(',', '.'))
                except ValueError:
                    continue
                
                if sku not in sales_data:
                    sales_data[sku] = {'units': 0.0, 'name': name_csv}
                
                sales_data[sku]['units'] += units
        
        # Step 3: Validate and calculate updates
        validation_results = []
        missing_skus = []
        
        for sku, data in sales_data.items():
            sold_qty = data['units']
            csv_name = data['name']
            product = holded_map.get(sku)
            
            if product:
                old_stock = product['stock']
                new_stock = old_stock - sold_qty
                validation_results.append({
                    'sku': sku,
                    'csv_name': csv_name,
                    'holded_name': product['name'],
                    'old_stock': old_stock,
                    'sold_qty': int(sold_qty),
                    'new_stock': new_stock,
                    'found': True,
                    'kind': product['kind']
                })
            else:
                missing_skus.append({
                    'sku': sku,
                    'csv_name': csv_name,
                    'sold_qty': int(sold_qty)
                })
        
        # Calculate totals
        total_units_sold = sum(item['units'] for item in sales_data.values())
        
        return {
            'file_info': {
                'filename': file.filename,
                'creation_date': creation_date_str,
                'total_rows': total_rows,
                'unique_skus': len(sales_data),
                'total_units_sold': int(total_units_sold)
            },
            'holded_info': {
                'total_products': count_products,
                'total_variants': count_variants,
                'total_skus': len(holded_map)
            },
            'validation_results': validation_results,
            'missing_skus': missing_skus,
            'summary': {
                'total_items': len(sales_data),
                'found_items': len(validation_results),
                'missing_items': len(missing_skus)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar validación: {str(e)}")


@app.get("/api/holded/stock-by-warehouse", tags=["Holded"], summary="Stock por Almacén")
async def get_stock_by_warehouse():
    """
    Obtiene el stock de todos los productos distribuidos por almacén desde Holded API.
    
    **Proceso:**
    1. Obtiene todos los almacenes
    2. Obtiene todos los productos (con nombre, SKU, variantes)
    3. Para cada almacén, obtiene el stock usando GET /warehouses/{warehouseId}/stock
    4. Consolida la información en una estructura tabular
    
    **Retorna:**
    - Lista de almacenes (ID y nombre)
    - Lista de productos con stock por cada almacén
    - Estadísticas resumen (total de almacenes, productos y variantes)
    
    **Errores posibles:**
    - 400: API key no configurada
    - 502: Error al comunicarse con Holded
    - 504: Timeout de conexión
    """
    # Check if API key is configured
    if not HOLDED_API_KEY:
        raise HTTPException(status_code=400, detail="API key de Holded no configurada")
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "key": HOLDED_API_KEY,
                "accept": "application/json"
            }
            
            # Step 1: Get all warehouses
            warehouses_url = "https://api.holded.com/api/invoicing/v1/warehouses"
            warehouses_response = await client.get(warehouses_url, headers=headers, timeout=30.0)
            
            if warehouses_response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Error al obtener almacenes: HTTP {warehouses_response.status_code}"
                )
            
            warehouses = warehouses_response.json()
            
            if not warehouses:
                return {
                    "status": "success",
                    "warehouses": [],
                    "products": [],
                    "summary": {
                        "total_warehouses": 0,
                        "total_products": 0,
                        "total_variants": 0
                    }
                }
            
            # Step 2: Get all products
            products_url = "https://api.holded.com/api/invoicing/v1/products"
            products_response = await client.get(products_url, headers=headers, timeout=30.0)
            
            if products_response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Error al obtener productos: HTTP {products_response.status_code}"
                )
            
            products = products_response.json()
            
            # Create a dictionary of products by ID for quick lookup
            products_dict = {p['id']: p for p in products}
            
            # Step 3: Get stock from each warehouse
            warehouse_stock_map = {}  # warehouse_id -> {product_id: stock_data}
            
            for warehouse in warehouses:
                warehouse_id = warehouse.get('id')
                if not warehouse_id:
                    continue
                
                stock_url = f"https://api.holded.com/api/invoicing/v1/warehouses/{warehouse_id}/stock"
                stock_response = await client.get(stock_url, headers=headers, timeout=30.0)
                
                if stock_response.status_code == 200:
                    stock_data = stock_response.json()
                    warehouse_products = stock_data.get('warehouse', {}).get('products', [])
                    
                    # Map stock by product ID
                    warehouse_stock_map[warehouse_id] = {}
                    for stock_item in warehouse_products:
                        product_id = stock_item.get('product_id')
                        if product_id:
                            warehouse_stock_map[warehouse_id][product_id] = {
                                'stock': stock_item.get('stock', 0),
                                'variants': stock_item.get('variants', {})
                            }
            
            # Step 4: Consolidate data into table format
            products_list = []
            total_products = 0
            total_variants = 0
            
            for product in products:
                product_id = product.get('id')
                product_name = product.get('name', 'N/A')
                product_sku = product.get('sku', '')
                
                # Add main product if it has SKU
                if product_sku:
                    stock_by_warehouse = {}
                    
                    for warehouse in warehouses:
                        warehouse_id = warehouse.get('id')
                        stock_info = warehouse_stock_map.get(warehouse_id, {}).get(product_id, {})
                        stock_by_warehouse[warehouse_id] = stock_info.get('stock', 0)
                    
                    products_list.append({
                        'sku': product_sku,
                        'name': product_name,
                        'type': 'principal',
                        'stock_by_warehouse': stock_by_warehouse
                    })
                    total_products += 1
                
                # Add variants if they exist
                variants = product.get('variants', [])
                for variant in variants:
                    variant_id = variant.get('id')
                    variant_sku = variant.get('sku', '')
                    variant_name = variant.get('name', '')
                    
                    if variant_sku:
                        stock_by_warehouse = {}
                        
                        for warehouse in warehouses:
                            warehouse_id = warehouse.get('id')
                            stock_info = warehouse_stock_map.get(warehouse_id, {}).get(product_id, {})
                            variants_stock = stock_info.get('variants', {})
                            stock_by_warehouse[warehouse_id] = variants_stock.get(variant_id, 0)
                        
                        full_name = f"{product_name} - {variant_name}" if variant_name else product_name
                        
                        products_list.append({
                            'sku': variant_sku,
                            'name': full_name,
                            'type': 'variante',
                            'stock_by_warehouse': stock_by_warehouse
                        })
                        total_variants += 1
            
            # Prepare warehouse list for response
            warehouses_list = [
                {
                    'id': wh.get('id'),
                    'name': wh.get('name', 'Sin nombre')
                }
                for wh in warehouses
            ]
            
            return {
                "status": "success",
                "warehouses": warehouses_list,
                "products": products_list,
                "summary": {
                    "total_warehouses": len(warehouses),
                    "total_products": total_products,
                    "total_variants": total_variants
                }
            }
    
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout al conectar con Holded API")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")



@app.put("/api/holded/stock/update", tags=["Holded"], summary="Actualizar Stock por SKU y Almacén")
async def update_stock_by_sku(request: StockUpdateRequest):
    """
    Actualiza el stock de un producto por SKU en un almacén específico.
    
    **Parámetros:**
    - `sku`: SKU del producto o variante a actualizar
    - `warehouse_id`: ID del almacén donde actualizar el stock
    - `stock_adjustment`: Ajuste de stock (positivo para sumar, negativo para restar, ej: +10, -5)
    - `description`: Descripción del ajuste (opcional, ej: 'Ajuste de stock', 'VENTAS 19 y 20 DIC')
    - `dry_run`: Si es True, simula la petición sin ejecutarla (default: False)
    
    **Proceso:**
    1. Busca el producto por SKU en todos los productos de Holded
    2. Valida que el almacén existe
    3. Obtiene el stock actual del warehouse
    4. Calcula el nuevo stock (stock_actual + ajuste)
    5. Si dry_run=True, simula la actualización y retorna los datos que se enviarían
    6. Si dry_run=False, ejecuta el ajuste del stock
    
    **Retorna:**
    - Información del producto encontrado
    - Datos de la petición (SKU, almacén, ajuste de stock)
    - Resultado de la operación (simulada o real)
    - Si es dry_run, muestra el payload que se enviaría
    
    **Errores posibles:**
    - 400: API key no configurada o datos inválidos
    - 404: Producto no encontrado o almacén no existe
    - 502: Error al comunicarse con Holded
    - 504: Timeout de conexión
    
    **Ejemplo de uso:**
    ```json
    {
        "sku": "PROD-001",
        "warehouse_id": "warehouse123",
        "stock_adjustment": -5,
        "description": "VENTAS 19 y 20 DIC",
        "dry_run": true
    }
    ```
    """
    # Check if API key is configured
    if not HOLDED_API_KEY:
        raise HTTPException(status_code=400, detail="API key de Holded no configurada")
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "key": HOLDED_API_KEY,
                "accept": "application/json",
                "content-type": "application/json"
            }
            
            # Step 1: Get all products to find the one with the given SKU
            products_url = "https://api.holded.com/api/invoicing/v1/products"
            products_response = await client.get(products_url, headers=headers, timeout=30.0)
            
            if products_response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Error al obtener productos de Holded: HTTP {products_response.status_code}"
                )
            
            products = products_response.json()
            
            # Find product or variant by SKU
            product_found = None
            product_id = None
            product_name = None
            is_variant = False
            variant_id = None
            
            for product in products:
                # Check main product SKU
                if product.get('sku') == request.sku:
                    product_found = product
                    product_id = product['id']
                    product_name = product.get('name', 'N/A')
                    is_variant = False
                    break
                
                # Check variants
                variants = product.get('variants', [])
                for variant in variants:
                    if variant.get('sku') == request.sku:
                        product_found = product
                        product_id = product['id']
                        variant_id = variant['id']
                        product_name = f"{product.get('name', 'N/A')} - {variant.get('name', '')}"
                        is_variant = True
                        break
                
                if product_found:
                    break
            
            if not product_found:
                raise HTTPException(
                    status_code=404,
                    detail=f"No se encontró ningún producto o variante con SKU: {request.sku}"
                )
            
            # Step 2: Validate that the warehouse exists
            warehouses_url = "https://api.holded.com/api/invoicing/v1/warehouses"
            warehouses_response = await client.get(warehouses_url, headers=headers, timeout=30.0)
            
            if warehouses_response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Error al obtener almacenes: HTTP {warehouses_response.status_code}"
                )
            
            warehouses = warehouses_response.json()
            warehouse_found = None
            
            for warehouse in warehouses:
                if warehouse.get('id') == request.warehouse_id:
                    warehouse_found = warehouse
                    break
            
            if not warehouse_found:
                raise HTTPException(
                    status_code=404,
                    detail=f"No se encontró el almacén con ID: {request.warehouse_id}"
                )
            
            # Step 3: Get current stock from warehouse
            stock_url = f"https://api.holded.com/api/invoicing/v1/warehouses/{request.warehouse_id}/stock"
            stock_response = await client.get(stock_url, headers=headers, timeout=30.0)
            
            current_stock = None
            if stock_response.status_code == 200:
                stock_data = stock_response.json()
                warehouse_products = stock_data.get('warehouse', {}).get('products', [])
                
                # Find the current stock for this product
                for stock_item in warehouse_products:
                    if stock_item.get('product_id') == product_id:
                        if is_variant and variant_id:
                            # For variants, look in the variants dict
                            variants_stock = stock_item.get('variants', {})
                            current_stock = variants_stock.get(variant_id, 0)
                        else:
                            # For main product
                            current_stock = stock_item.get('stock', 0)
                        break
            
            # If stock not found in warehouse, it means it's 0
            if current_stock is None:
                current_stock = 0
            
            # Step 4: Prepare the update payload
            # CRITICAL: According to Holded API documentation, the structure must use
            # warehouse ID and product/variant ID as KEYS, not as values
            # Correct format:
            # {
            #   "stock": {
            #     "WAREHOUSE_ID": {
            #       "PRODUCT_ID or VARIANT_ID": stock_value
            #     }
            #   }
            # }
            
            # Determine which ID to use as the key
            item_id = variant_id if is_variant else product_id
            
            # Build the nested structure with stock adjustment
            stock_payload = {
                "stock": {
                    request.warehouse_id: {
                        item_id: request.stock_adjustment
                    }
                }
            }
            
            # Add description if provided
            if request.description:
                stock_payload["desc"] = request.description
            
            # Prepare response data
            response_data = {
                "status": "dry_run" if request.dry_run else "success",
                "product_info": {
                    "sku": request.sku,
                    "product_id": product_id,
                    "product_name": product_name,
                    "is_variant": is_variant,
                    "variant_id": variant_id if is_variant else None
                },
                "warehouse_info": {
                    "warehouse_id": request.warehouse_id,
                    "warehouse_name": warehouse_found.get('name', 'N/A')
                },
                "stock_update": {
                    "current_stock": current_stock,
                    "stock_adjustment": request.stock_adjustment,
                    "new_stock": current_stock + request.stock_adjustment,
                    "description": request.description if request.description else None
                }
            }
            
            # Step 5: Execute or simulate the update
            if request.dry_run:
                # Dry run mode - just return what would be sent
                response_data["message"] = "Simulación exitosa - No se realizó ninguna actualización real"
                response_data["api_call"] = {
                    "method": "PUT",
                    "url": f"https://api.holded.com/api/invoicing/v1/products/{product_id}/stock",
                    "payload": stock_payload
                }
            else:
                # Real update
                update_url = f"https://api.holded.com/api/invoicing/v1/products/{product_id}/stock"
                
                update_response = await client.put(
                    update_url,
                    headers=headers,
                    json=stock_payload,
                    timeout=30.0
                )
                
                if update_response.status_code == 200:
                    response_data["message"] = "Stock actualizado exitosamente"
                    response_data["holded_response"] = update_response.json()
                elif update_response.status_code == 204:
                    # Some APIs return 204 No Content on successful update
                    response_data["message"] = "Stock actualizado exitosamente"
                else:
                    raise HTTPException(
                        status_code=502,
                        detail=f"Error al actualizar stock en Holded: HTTP {update_response.status_code} - {update_response.text}"
                    )
            
            return response_data
    
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout al conectar con Holded API")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================================================================
# GOOGLE CLOUD STORAGE ENDPOINTS
# ============================================================================

@app.get("/api/gcs/health", tags=["Cloud Storage"], summary="Verificar Configuración de GCS")
async def gcs_health():
    """
    Verifica la configuración y conectividad con Google Cloud Storage.
    
    **Retorna:**
    - Estado de configuración (si las credenciales están configuradas)
    - Nombre del bucket configurado
    - Resultado del test de conexión
    - Información sobre el bucket (si la conexión es exitosa)
    """
    credentials_configured = bool(GCS_CREDENTIALS_BASE64)
    
    response = {
        "configured": credentials_configured,
        "bucket_name": GCS_BUCKET_NAME,
        "connection_test": {
            "status": "not_tested",
            "message": ""
        }
    }
    
    if credentials_configured:
        try:
            client = get_gcs_client()
            bucket = client.bucket(GCS_BUCKET_NAME)
            
            # Test if bucket exists and is accessible
            if bucket.exists():
                response["connection_test"]["status"] = "success"
                response["connection_test"]["message"] = "Conexión exitosa con Google Cloud Storage"
                response["connection_test"]["bucket_exists"] = True
            else:
                response["connection_test"]["status"] = "error"
                response["connection_test"]["message"] = f"El bucket {GCS_BUCKET_NAME} no existe o no es accesible"
                response["connection_test"]["bucket_exists"] = False
        
        except HTTPException:
            raise
        except Exception as e:
            response["connection_test"]["status"] = "error"
            response["connection_test"]["message"] = f"Error: {str(e)}"
    else:
        response["connection_test"]["status"] = "not_configured"
        response["connection_test"]["message"] = "Credenciales GCS no configuradas"
    
    return response


@app.get("/api/gcs/files", tags=["Cloud Storage"], summary="Listar Archivos del Bucket")
async def list_gcs_files(prefix: Optional[str] = None, max_results: Optional[int] = 1000):
    """
    Lista todos los archivos en el bucket de Google Cloud Storage.
    
    **Parámetros opcionales:**
    - `prefix`: Filtrar archivos por prefijo (ej: 'reports/' para listar solo archivos en la carpeta reports)
    - `max_results`: Número máximo de resultados a retornar (default: 1000)
    
    **Retorna:**
    - Lista de archivos con metadata completa:
      - name: nombre del archivo
      - size: tamaño en bytes
      - size_mb: tamaño en megabytes
      - created: fecha de creación
      - updated: fecha de última modificación
      - content_type: tipo MIME del archivo
      - md5_hash: hash MD5 del contenido
      - public_url: URL pública (si el archivo es público)
    - Contador total de archivos
    - Tamaño total en el bucket
    
    **Errores posibles:**
    - 400: Credenciales no configuradas
    - 500: Error al acceder al bucket
    """
    try:
        client = get_gcs_client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        
        # List blobs with optional prefix filter
        blobs = list(bucket.list_blobs(prefix=prefix, max_results=max_results))
        
        files = []
        total_size = 0
        
        for blob in blobs:
            file_info = {
                "name": blob.name,
                "size": blob.size,
                "size_mb": round(blob.size / (1024 * 1024), 2) if blob.size else 0,
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "content_type": blob.content_type,
                "md5_hash": blob.md5_hash,
                "public_url": blob.public_url if blob.public_url else None
            }
            files.append(file_info)
            total_size += blob.size if blob.size else 0
        
        return {
            "status": "success",
            "bucket": GCS_BUCKET_NAME,
            "prefix": prefix,
            "count": len(files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "files": files
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar archivos: {str(e)}")


@app.post("/api/gcs/upload", tags=["Cloud Storage"], summary="Subir Archivo al Bucket")
async def upload_to_gcs(file: UploadFile = File(...), destination_path: Optional[str] = None):
    """
    Sube un archivo al bucket de Google Cloud Storage.
    
    **Parámetros:**
    - `file`: Archivo a subir
    - `destination_path`: Ruta de destino en el bucket (opcional, por defecto usa el nombre del archivo)
    
    **Retorna:**
    - Información del archivo subido
    - URL pública del archivo
    - Metadata completa
    
    **Errores posibles:**
    - 400: Credenciales no configuradas
    - 500: Error al subir el archivo
    """
    try:
        client = get_gcs_client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        
        # Use provided destination path or default to filename
        blob_name = destination_path if destination_path else file.filename
        blob = bucket.blob(blob_name)
        
        # Read file content
        contents = await file.read()
        
        # Upload to GCS
        blob.upload_from_string(
            contents,
            content_type=file.content_type
        )
        
        # Reload to get updated metadata
        blob.reload()
        
        return {
            "status": "success",
            "message": "Archivo subido exitosamente",
            "file": {
                "name": blob.name,
                "size": blob.size,
                "size_mb": round(blob.size / (1024 * 1024), 2) if blob.size else 0,
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "content_type": blob.content_type,
                "md5_hash": blob.md5_hash,
                "public_url": blob.public_url,
                "bucket": GCS_BUCKET_NAME
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")


@app.get("/api/gcs/download/{file_path:path}", tags=["Cloud Storage"], summary="Descargar Archivo del Bucket")
async def download_from_gcs(file_path: str):
    """
    Descarga un archivo del bucket de Google Cloud Storage.
    
    **Parámetros:**
    - `file_path`: Ruta del archivo en el bucket
    
    **Retorna:**
    - Archivo como respuesta de streaming
    
    **Errores posibles:**
    - 400: Credenciales no configuradas
    - 404: Archivo no encontrado
    - 500: Error al descargar el archivo
    """
    try:
        client = get_gcs_client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(file_path)
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {file_path}")
        
        # Download as bytes
        file_bytes = blob.download_as_bytes()
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type=blob.content_type or "application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={Path(file_path).name}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al descargar archivo: {str(e)}")


@app.delete("/api/gcs/delete/{file_path:path}", tags=["Cloud Storage"], summary="Eliminar Archivo del Bucket")
async def delete_from_gcs(file_path: str):
    """
    Elimina un archivo del bucket de Google Cloud Storage.
    
    **Parámetros:**
    - `file_path`: Ruta del archivo en el bucket
    
    **Retorna:**
    - Confirmación de eliminación
    - Información del archivo eliminado
    
    **Errores posibles:**
    - 400: Credenciales no configuradas
    - 404: Archivo no encontrado
    - 500: Error al eliminar el archivo
    """
    try:
        client = get_gcs_client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(file_path)
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {file_path}")
        
        # Get file info before deleting
        file_info = {
            "name": blob.name,
            "size": blob.size,
            "size_mb": round(blob.size / (1024 * 1024), 2) if blob.size else 0,
            "content_type": blob.content_type
        }
        
        # Delete the blob
        blob.delete()
        
        return {
            "status": "success",
            "message": "Archivo eliminado exitosamente",
            "deleted_file": file_info
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar archivo: {str(e)}")


@app.get("/api/gcs/metadata/{file_path:path}", tags=["Cloud Storage"], summary="Obtener Metadata de Archivo")
async def get_file_metadata(file_path: str):
    """
    Obtiene la metadata completa de un archivo en el bucket.
    
    **Parámetros:**
    - `file_path`: Ruta del archivo en el bucket
    
    **Retorna:**
    - Metadata completa del archivo:
      - name: nombre del archivo
      - size: tamaño en bytes y MB
      - created: fecha de creación
      - updated: fecha de última modificación
      - content_type: tipo MIME
      - md5_hash: hash MD5
      - crc32c: checksum CRC32C
      - etag: ETag del archivo
      - generation: versión del archivo
      - metageneration: versión de metadata
      - storage_class: clase de almacenamiento
      - public_url: URL pública
    
    **Errores posibles:**
    - 400: Credenciales no configuradas
    - 404: Archivo no encontrado
    - 500: Error al obtener metadata
    """
    try:
        client = get_gcs_client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(file_path)
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {file_path}")
        
        # Reload to get fresh metadata
        blob.reload()
        
        return {
            "status": "success",
            "file": {
                "name": blob.name,
                "bucket": GCS_BUCKET_NAME,
                "size": {
                    "bytes": blob.size,
                    "mb": round(blob.size / (1024 * 1024), 2) if blob.size else 0,
                    "kb": round(blob.size / 1024, 2) if blob.size else 0
                },
                "dates": {
                    "created": blob.time_created.isoformat() if blob.time_created else None,
                    "updated": blob.updated.isoformat() if blob.updated else None,
                },
                "checksums": {
                    "md5_hash": blob.md5_hash,
                    "crc32c": blob.crc32c,
                    "etag": blob.etag
                },
                "content_type": blob.content_type,
                "storage_class": blob.storage_class,
                "generation": blob.generation,
                "metageneration": blob.metageneration,
                "public_url": blob.public_url,
                "media_link": blob.media_link
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener metadata: {str(e)}")

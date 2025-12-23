# FastAPI Hello World - Railway Deployment

## 🚀 Desplegar en Railway

### Opción 1: Desde GitHub (Recomendado)
1. Sube este código a un repositorio de GitHub
2. Ve a [railway.app](https://railway.app)
3. Haz clic en "Start a New Project"
4. Selecciona "Deploy from GitHub repo"
5. Conecta tu repositorio
6. Railway detectará automáticamente que es un proyecto Python y lo desplegará

### Opción 2: Desde Railway CLI
```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login en Railway
railway login

# Inicializar proyecto
railway init

# Desplegar
railway up
```

## 🧪 Probar localmente

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Mac/Linux

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
uvicorn main:app --reload
```

Luego visita: http://localhost:8000

## 📝 Endpoints

### Sistema
- `GET /` - Frontend principal con upload de CSV
- `GET /health` - Health check general
- `GET /docs` - Documentación interactiva de FastAPI (Swagger UI)
- `GET /redoc` - Documentación alternativa (ReDoc)

### Holded API
- `GET /api/holded/health` - Verifica la configuración de Holded API
- `GET /api/holded/warehouses` - Listar almacenes de Holded
- `GET /api/holded/stock-by-warehouse` - Obtener stock de todos los productos distribuidos por almacén
- `PUT /api/holded/stock/update` - **Actualizar stock de producto por SKU y almacén**

### Archivos
- `POST /api/upload-csv` - Subir y procesar archivo CSV
- `POST /api/stock/validate` - Validar stock contra Holded

### Cloud Storage
- `GET /api/gcs/health` - Verificar conexión y configuración de GCS
- `GET /api/gcs/files` - Listar archivos en el bucket
- `POST /api/gcs/upload` - Subir archivo al bucket
- `GET /api/gcs/download/{file_path}` - Descargar archivo
- `DELETE /api/gcs/delete/{file_path}` - Eliminar archivo
- `GET /api/gcs/metadata/{file_path}` - Obtener metadata completa


---

## 📦 Actualizar Stock por SKU y Almacén

### `PUT /api/holded/stock/update`

Actualiza el stock de un producto en un almacén específico de Holded, identificándolo por su SKU.

#### Características

- ✅ Busca automáticamente el producto por SKU (soporta productos y variantes)
- ✅ Valida que el almacén existe
- ✅ Permite ajustes positivos (añadir stock) o negativos (restar stock)
- ✅ Opción de dry-run para simular sin ejecutar
- ✅ Incluye descripción personalizada para el log de Holded
- ✅ Muestra stock actual, ajuste y stock resultante

#### Parámetros

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `sku` | string | ✅ | SKU del producto o variante |
| `warehouse_id` | string | ✅ | ID del almacén donde actualizar el stock |
| `stock_adjustment` | number | ✅ | Ajuste de stock: positivo para añadir, negativo para restar |
| `description` | string | ❌ | Descripción del ajuste (ej: "VENTAS 19 y 20 DIC") |
| `dry_run` | boolean | ❌ | Si es `true`, simula sin ejecutar (default: `false`) |

#### Ejemplos de Uso

##### 1. Simular resta de stock (dry-run)
```bash
curl -X PUT http://localhost:8000/api/holded/stock/update \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "5G-3XF++",
    "warehouse_id": "684d465d86708f8d2d0aaee5",
    "stock_adjustment": -5,
    "description": "VENTAS 19 y 20 DIC",
    "dry_run": true
  }'
```

**Respuesta:**
```json
{
  "status": "dry_run",
  "product_info": {
    "sku": "5G-3XF++",
    "product_id": "6917514d421649f142028a0d",
    "product_name": "3X FILTRÉ ++ - ",
    "is_variant": true,
    "variant_id": "6917514d421649f142028a0f"
  },
  "warehouse_info": {
    "warehouse_id": "684d465d86708f8d2d0aaee5",
    "warehouse_name": "TIENDA SALAMANCA"
  },
  "stock_update": {
    "current_stock": 10,
    "stock_adjustment": -5,
    "new_stock": 5,
    "description": "VENTAS 19 y 20 DIC"
  },
  "message": "Simulación exitosa - No se realizó ninguna actualización real",
  "api_call": {
    "method": "PUT",
    "url": "https://api.holded.com/api/invoicing/v1/products/6917514d421649f142028a0d/stock",
    "payload": {
      "stock": {
        "684d465d86708f8d2d0aaee5": {
          "6917514d421649f142028a0f": -5
        }
      },
      "desc": "VENTAS 19 y 20 DIC"
    }
  }
}
```

##### 2. Añadir stock real
```bash
curl -X PUT http://localhost:8000/api/holded/stock/update \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "PROD-001",
    "warehouse_id": "warehouse123",
    "stock_adjustment": 25,
    "description": "AJUSTE POR RECUENTO",
    "dry_run": false
  }'
```

##### 3. Restar stock sin descripción
```bash
curl -X PUT http://localhost:8000/api/holded/stock/update \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "2G-XF",
    "warehouse_id": "warehouse123",
    "stock_adjustment": -3,
    "dry_run": false
  }'
```

#### Casos de Uso

- **Ajustes de ventas**: Restar unidades vendidas con descripción informativa
- **Ajustes de inventario**: Corregir stock tras recuento físico
- **Transferencias**: Restar de un almacén y añadir a otro
- **Devoluciones**: Añadir unidades devueltas por clientes
- **Simulación**: Verificar cambios antes de aplicarlos con `dry_run: true`

#### Errores Comunes

- **404**: SKU no encontrado o warehouse no existe
- **400**: API key no configurada
- **502**: Error al comunicarse con Holded API
- **504**: Timeout de conexión

## 🔐 Configuración de Variables de Entorno

### Variables requeridas para Holded

```bash
HOLDED_API_KEY=tu_api_key_aqui
HOLDED_BASE_URL=https://api.holded.com/api/invoicing/v1/products
```

### Variables requeridas para Google Cloud Storage

```bash
GCS_CREDENTIALS_BASE64=tu_json_credenciales_base64
```

**Generar GCS_CREDENTIALS_BASE64:**
1. Descarga el JSON de la cuenta de servicio de GCP.
2. Codifícalo en base64:
   ```bash
   # Linux/Mac
   base64 -i credentials.json -o credentials_base64.txt
   
   # Copia el contenido de credentials_base64.txt
   cat credentials_base64.txt | pbcopy  # En Mac
   ```


### Configuración Local

1. Copia el archivo de ejemplo:
```bash
cp .env.example .env
```

2. Edita `.env` y añade tu API key de Holded

3. El archivo `.env` se cargará automáticamente al iniciar la aplicación

### Configuración en Railway

1. Ve a tu proyecto en Railway
2. Haz clic en la pestaña "Variables"
3. Añade las siguientes variables:
   - `HOLDED_API_KEY`: Tu API key de Holded
   - `HOLDED_BASE_URL`: `https://api.holded.com/api/invoicing/v1/products`
   - `GCS_CREDENTIALS_BASE64`: El contenido base64 de tu JSON de servicio

4. Railway redesplegará automáticamente tu aplicación

### Verificar configuración

Después de configurar las variables, verifica que todo funciona visitando:
- Local: `http://localhost:8000/api/holded/health`
- Railway: `https://tu-app.railway.app/api/holded/health`

La respuesta mostrará:
- Si las variables están configuradas
- Los últimos 4 caracteres de tu API key (para verificación segura)
- El resultado de una prueba de conexión real con la API de Holded


## 🔧 Archivos del proyecto

- `main.py` - Punto de entrada de la aplicación
- `app/` - Código fuente de la aplicación
  - `api/routes/` - Definición de endpoints (Holded, GCS, CSV)
  - `services/` - Lógica de negocio e integraciones
  - `models/` - Modelos de datos Pydantic
  - `core/` - Configuración y variables de entorno
### `POST /api/holded/stock/update-from-gcs`

Actualiza masivamente el stock en Holded tomando como fuente un archivo CSV alojado en Google Cloud Storage. Ideal para integraciones automáticas donde se sube un reporte de ventas a GCS.

#### Características

- ✅ **Lectura desde GCS**: Descarga y procesa archivos directamente de la nube (`gs://...`).
- ✅ **Soporte de Encoding**: Detecta automáticamente UTF-8 o Latin-1 (común en Excel).
- ✅ **Mapeo Inteligente**:
    - Busca productos por SKU o código de barras.
    - Asigna almacenes basándose en el nombre de la terminal (con soporte para nombres como "Tienda Cáceres", "Tienda Murcia", etc.).
- ✅ **Cálculo de Stock**:
    - Resta las unidades vendidas ("UNIDADES" del CSV) al stock actual de Holded.
    - Soporta productos simples y variantes.
- ✅ **Respuesta Detallada**:
    - Muestra el stock *antes* y *después* de la actualización.
    - Reporta errores específicos (fila, SKU, producto) sin detener el proceso completo.
- ✅ **Dry Run**: Por defecto (`dry_run=true`) simula todo el proceso sin tocar Holded.

#### Parámetros (`JSON`)

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `gs_uri` | string | ✅ | URI del archivo en GCS (ej: `gs://bucket/archivo.csv`) |
| `dry_run` | boolean | ❌ | Si es `true`, simula. Si es `false`, ejecuta. (Default: `true`) |

#### Formato CSV Esperado

El archivo debe usar punto y coma (`;`) como separador.

| Columna (Header) | Descripción |
|------------------|-------------|
| `TERMINAL` | Nombre del almacén/tienda (ej: "TIENDA CACERES") |
| `C.BARRAS ARTICULO` | SKU o Código de barras del producto |
| `UNIDADES` | Cantidad vendida (se restará del stock) |
| `ARTÍCULO` / `ARTICULO` | Nombre del producto (opcional, para logs de error) |

#### Ejemplo de Uso

**Petición:**
```bash
curl -X POST "http://localhost:8000/api/holded/stock/update-from-gcs" \
     -H "Content-Type: application/json" \
     -d '{
           "gs_uri": "gs://mi-bucket/ventas-caceres.csv",
           "dry_run": true
         }'
```

**Respuesta:**
```json
{
  "processed": 43,
  "updated": 1,
  "errors": [
    {
      "row": 35,
      "sku": "156517431",
      "product": "PRODUCTO DESC",
      "units": 2.0,
      "error": "SKU no encontrado",
      "terminal": "TIENDA CACERES"
    }
  ],
  "updates": [
    {
      "row": 0,
      "sku": "SKU-123",
      "product": "Producto Ejemplo",
      "warehouse": "TIENDA CACERES",
      "units_sold": 5.0,
      "adjustment": -5.0,
      "current_stock": 20,
      "new_stock": 15.0,
      "status": "simulated"
    }
  ]
}
```
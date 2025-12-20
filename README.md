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

- `GET /` - Frontend principal con upload de CSV
- `GET /health` - Health check general
- `GET /api/holded/health` - Verifica la configuración de Holded API
- `POST /api/upload-csv` - Subir y procesar archivo CSV
- `GET /docs` - Documentación interactiva de FastAPI (Swagger UI)

## 🔐 Configuración de Variables de Entorno

### Variables requeridas para Holded

```bash
HOLDED_API_KEY=tu_api_key_aqui
HOLDED_BASE_URL=https://api.holded.com/api/invoicing/v1/products
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

- `main.py` - Aplicación FastAPI
- `requirements.txt` - Dependencias de Python
- `Procfile` - Comando para iniciar el servidor en Railway
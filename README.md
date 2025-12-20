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

- `GET /` - Hello World
- `GET /health` - Health check
- `GET /docs` - Documentación interactiva de FastAPI (Swagger UI)

## 🔧 Archivos del proyecto

- `main.py` - Aplicación FastAPI
- `requirements.txt` - Dependencias de Python
- `Procfile` - Comando para iniciar el servidor en Railway
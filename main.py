from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
import pandas as pd
import io
from dotenv import load_dotenv
import httpx

# Load environment variables (try .env.local first, then .env)
load_dotenv(".env.local")
load_dotenv()

# Holded configuration
HOLDED_API_KEY = os.getenv("HOLDED_API_KEY", "")
HOLDED_BASE_URL = os.getenv("HOLDED_BASE_URL", "https://api.holded.com/api/invoicing/v1/products")


app = FastAPI()

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

@app.get("/")
async def read_root():
    """Serve the main frontend page"""
    return FileResponse(static_dir / "index.html")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/holded/health")
async def holded_health():
    """
    Check Holded API configuration and connectivity
    Returns:
    - Configuration status (if API key is set)
    - Last 4 characters of API key (for verification)
    - Base URL
    - Connection test result
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


@app.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload and process a CSV file
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

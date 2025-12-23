
from fastapi import APIRouter, HTTPException
from typing import Optional
import httpx
from app.core.config import settings
from app.models.schemas import StockUpdateRequest, StockUpdateFromGCSRequest, GCSStockUpdateResponse
from app.services import holded as holded_service

router = APIRouter()

@router.get("/health", summary="Verificar Configuración de Holded")
async def holded_health():
    """
    Verifica la configuración y conectividad con Holded API.
    """
    # Check if API key is configured
    api_key_configured = bool(settings.HOLDED_API_KEY)
    
    # Get last 4 characters of API key (or empty if not set)
    api_key_suffix = settings.HOLDED_API_KEY[-4:] if len(settings.HOLDED_API_KEY) >= 4 else ""
    
    # Prepare response
    response = {
        "configured": api_key_configured,
        "api_key_suffix": f"...{api_key_suffix}" if api_key_suffix else "NO CONFIGURADA",
        "base_url": settings.HOLDED_BASE_URL,
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
                    "key": settings.HOLDED_API_KEY,
                    "Accept": "application/json"
                }
                test_response = await client.get(settings.HOLDED_BASE_URL, headers=headers, timeout=10.0)
                
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

@router.get("/warehouses", summary="Listar Almacenes")
async def get_holded_warehouses():
    """
    Obtiene la lista de almacenes desde Holded API.
    """
    try:
        data = await holded_service.get_holded_warehouses()
        return {
            "status": "success",
            "count": len(data) if isinstance(data, list) else 0,
            "warehouses": data
        }
    except Exception as e:
        status_code = 500
        if "401" in str(e): status_code = 401
        elif "Timeout" in str(e): status_code = 504
        
        raise HTTPException(status_code=status_code, detail=str(e))

@router.get("/stock-by-warehouse", summary="Stock por Almacén")
async def get_stock_by_warehouse():
    """
    Obtiene el stock de todos los productos distribuidos por almacén.
    """
    try:
        return await holded_service.get_stock_by_warehouse()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/stock/update", summary="Actualizar Stock por SKU y Almacén")
async def update_stock_by_sku(request: StockUpdateRequest):
    """
    Actualiza el stock de un producto por SKU en un almacén específico.
    """
    try:
        return await holded_service.update_stock_by_sku(request)
    except Exception as e:
         status_code = 500
         if "No se encontró" in str(e): status_code = 404
         raise HTTPException(status_code=status_code, detail=str(e))

@router.post("/stock/update-from-gcs", summary="Actualizar Stock desde CSV en GCS", response_model=GCSStockUpdateResponse)
async def update_stock_from_gcs(request: StockUpdateFromGCSRequest):
    """
    Actualiza el stock en Holded procesando un archivo CSV almacenado en GCS.
    """
    try:
        return await holded_service.update_stock_from_gcs(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

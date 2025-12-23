
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Optional
import io
from pathlib import Path
from app.core.config import settings
from app.services.gcs import get_gcs_client

router = APIRouter()

@router.get("/health", summary="Verificar Configuración de GCS")
async def gcs_health():
    """Verifica la configuración y conectividad con GCS."""
    credentials_configured = bool(settings.GCS_CREDENTIALS_BASE64)
    
    response = {
        "configured": credentials_configured,
        "bucket_name": settings.GCS_BUCKET_NAME,
        "connection_test": {
            "status": "not_tested",
            "message": ""
        }
    }
    
    if credentials_configured:
        try:
            client = get_gcs_client()
            bucket = client.bucket(settings.GCS_BUCKET_NAME)
            
            if bucket.exists():
                response["connection_test"]["status"] = "success"
                response["connection_test"]["message"] = "Conexión exitosa con Google Cloud Storage"
                response["connection_test"]["bucket_exists"] = True
            else:
                response["connection_test"]["status"] = "error"
                response["connection_test"]["message"] = f"El bucket {settings.GCS_BUCKET_NAME} no existe o no es accesible"
                response["connection_test"]["bucket_exists"] = False
        except Exception as e:
            response["connection_test"]["status"] = "error"
            response["connection_test"]["message"] = f"Error: {str(e)}"
    else:
        response["connection_test"]["status"] = "not_configured"
        response["connection_test"]["message"] = "Credenciales GCS no configuradas"
    
    return response

@router.get("/files", summary="Listar Archivos del Bucket")
async def list_gcs_files(prefix: Optional[str] = None, max_results: Optional[int] = 1000):
    try:
        client = get_gcs_client()
        bucket = client.bucket(settings.GCS_BUCKET_NAME)
        
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
            "bucket": settings.GCS_BUCKET_NAME,
            "prefix": prefix,
            "count": len(files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "files": files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar archivos: {str(e)}")

@router.post("/upload", summary="Subir Archivo al Bucket")
async def upload_to_gcs(file: UploadFile = File(...), destination_path: Optional[str] = None):
    try:
        client = get_gcs_client()
        bucket = client.bucket(settings.GCS_BUCKET_NAME)
        
        blob_name = destination_path if destination_path else file.filename
        blob = bucket.blob(blob_name)
        
        contents = await file.read()
        
        blob.upload_from_string(
            contents,
            content_type=file.content_type
        )
        
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
                "bucket": settings.GCS_BUCKET_NAME
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")

@router.get("/download/{file_path:path}", summary="Descargar Archivo del Bucket")
async def download_from_gcs(file_path: str):
    try:
        client = get_gcs_client()
        bucket = client.bucket(settings.GCS_BUCKET_NAME)
        blob = bucket.blob(file_path)
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {file_path}")
        
        file_bytes = blob.download_as_bytes()
        
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

@router.delete("/delete/{file_path:path}", summary="Eliminar Archivo del Bucket")
async def delete_from_gcs(file_path: str):
    try:
        client = get_gcs_client()
        bucket = client.bucket(settings.GCS_BUCKET_NAME)
        blob = bucket.blob(file_path)
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {file_path}")
        
        file_info = {
            "name": blob.name,
            "size": blob.size,
            "size_mb": round(blob.size / (1024 * 1024), 2) if blob.size else 0,
            "content_type": blob.content_type
        }
        
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

@router.get("/metadata/{file_path:path}", summary="Obtener Metadata de Archivo")
async def get_file_metadata(file_path: str):
    try:
        client = get_gcs_client()
        bucket = client.bucket(settings.GCS_BUCKET_NAME)
        blob = bucket.blob(file_path)
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {file_path}")
        
        blob.reload()
        
        return {
            "status": "success",
            "file": {
                "name": blob.name,
                "bucket": settings.GCS_BUCKET_NAME,
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

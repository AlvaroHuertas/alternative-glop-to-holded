
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.services import csv_proc

router = APIRouter()

@router.post("/upload-csv", summary="Subir y Procesar CSV")
async def upload_csv(file: UploadFile = File(...)):
    """
    Sube y procesa un archivo CSV.
    """
    try:
        return await csv_proc.upload_csv_file(file)
    except Exception as e:
         status_code = 500
         if "archivo debe ser CSV" in str(e): status_code = 400
         raise HTTPException(status_code=status_code, detail=str(e))

@router.post("/stock/validate", summary="Validar Stock contra Holded")
async def validate_stock(file: UploadFile = File(...)):
    """
    Valida stock contra Holded API.
    """
    try:
        return await csv_proc.validate_stock_against_holded(file)
    except Exception as e:
         status_code = 500
         if "archivo debe ser CSV" in str(e): status_code = 400
         elif "Holded" in str(e) and "HTTP" in str(e): status_code = 502
         raise HTTPException(status_code=status_code, detail=str(e))

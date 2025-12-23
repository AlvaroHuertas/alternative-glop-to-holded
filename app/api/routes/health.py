
from fastapi import APIRouter

router = APIRouter()

@router.get("", summary="Health Check")
async def health():
    """Verifica que la API esté funcionando correctamente"""
    return {"status": "ok"}

from pydantic import BaseModel, Field
from typing import Optional, List

class StockUpdateRequest(BaseModel):
    """Request model for updating product stock"""
    sku: str = Field(..., description="SKU del producto a actualizar")
    warehouse_id: str = Field(..., description="ID del almacén donde actualizar el stock")
    stock_adjustment: float = Field(..., description="Ajuste de stock: positivo para añadir, negativo para restar (ej: +10, -5)")
    description: str = Field(default="", description="Descripción del ajuste de stock (ej: 'Ajuste de stock', 'VENTAS 19 y 20 DIC')")
    dry_run: bool = Field(default=False, description="Si es True, simula la petición sin ejecutarla")

class StockUpdateFromGCSRequest(BaseModel):
    gs_uri: str = Field(..., description="URI del archivo CSV en GCS (ej: gs://bucket/file.csv)")
    dry_run: bool = Field(default=True, description="Si es True, simula la actualización sin cambios reales")

class UpdateErrorDetail(BaseModel):
    row: int = Field(..., description="Número de fila en el CSV (0-indexed)")
    sku: str = Field(..., description="SKU del producto")
    product: str = Field("Unknown", description="Nombre del producto extraído del CSV")
    units: Optional[float] = Field(None, description="Unidades vendidas (del CSV)")
    terminal: str = Field(..., description="Nombre de la terminal/almacén")
    error: str = Field(..., description="Detalle del error")

class StockUpdateResult(BaseModel):
    row: int = Field(..., description="Número de fila en el CSV")
    sku: str = Field(..., description="SKU del producto")
    product: str = Field(..., description="Nombre del producto (Holded)")
    warehouse: str = Field(..., description="Nombre del almacén (CSV)")
    warehouse_id: str = Field(..., description="ID del almacén (Holded)")
    units_sold: float = Field(..., description="Unidades del CSV (vendidas)")
    adjustment: float = Field(..., description="Ajuste calculado (-unidades)")
    current_stock: float = Field(..., description="Stock antes de actualizar")
    new_stock: float = Field(..., description="Stock calculado después del ajuste")
    status: str = Field(..., description="success, error, simulated")
    error_detail: Optional[str] = Field(None, description="Detalle del error si falló")

class GCSStockUpdateResponse(BaseModel):
    processed: int = Field(..., description="Total de filas procesadas")
    updated: int = Field(..., description="Total de actualizaciones exitosas (o simuladas)")
    errors: List[UpdateErrorDetail] = Field(..., description="Lista de errores encontrados")
    updates: List[StockUpdateResult] = Field(..., description="Detalle de las actualizaciones")

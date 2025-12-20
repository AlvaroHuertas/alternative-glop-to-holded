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


@app.get("/api/holded/warehouses")
async def get_holded_warehouses():
    """
    Get list of warehouses from Holded API
    Returns:
    - List of warehouses with their details
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


@app.post("/api/stock/validate")
async def validate_stock(file: UploadFile = File(...)):
    """
    Validate stock against Holded API
    Processes a CSV file with sales data and checks against current Holded inventory
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



import os
import csv
import datetime
import pandas as pd
import io
import httpx
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.core.config import settings

# Create uploads directory
UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

async def upload_csv_file(file: UploadFile):
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="El archivo debe ser CSV")
    
    try:
        # Read file content
        contents = await file.read()
        
        # Save file
        file_path = UPLOADS_DIR / file.filename
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

async def validate_stock_against_holded(file: UploadFile):
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="El archivo debe ser CSV")
    
    try:
        # Read file content
        contents = await file.read()
        
        # Save file temporarily
        file_path = UPLOADS_DIR / file.filename
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
        if not settings.HOLDED_API_KEY:
            raise HTTPException(status_code=400, detail="API key de Holded no configurada")
        
        headers = {
            "key": settings.HOLDED_API_KEY,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            holded_response = await client.get(settings.HOLDED_BASE_URL, headers=headers, timeout=30.0)
            
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

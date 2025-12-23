
import httpx
import pandas as pd
import io
import json
import datetime
from datetime import timezone
from app.core.config import settings
from app.models.schemas import StockUpdateRequest, StockUpdateFromGCSRequest
from app.services.gcs import get_gcs_client

async def get_holded_warehouses():
    if not settings.HOLDED_API_KEY:
        raise Exception("API key de Holded no configurada")
    
    async with httpx.AsyncClient() as client:
        headers = {
            "key": settings.HOLDED_API_KEY,
            "accept": "application/json"
        }
        
        warehouses_url = "https://api.holded.com/api/invoicing/v1/warehouses"
        response = await client.get(warehouses_url, headers=headers, timeout=30.0)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise Exception("API key inválida o sin permisos")
        else:
            raise Exception(f"Error al obtener almacenes de Holded: HTTP {response.status_code}")

async def get_stock_by_warehouse():
    if not settings.HOLDED_API_KEY:
        raise Exception("API key de Holded no configurada")
    
    async with httpx.AsyncClient() as client:
        headers = {
            "key": settings.HOLDED_API_KEY,
            "accept": "application/json"
        }
        
        # Step 1: Get all warehouses
        warehouses_url = "https://api.holded.com/api/invoicing/v1/warehouses"
        warehouses_response = await client.get(warehouses_url, headers=headers, timeout=30.0)
        
        if warehouses_response.status_code != 200:
            raise Exception(f"Error al obtener almacenes: HTTP {warehouses_response.status_code}")
        
        warehouses = warehouses_response.json()
        
        if not warehouses:
            return {
                "status": "success",
                "warehouses": [],
                "products": [],
                "summary": {
                    "total_warehouses": 0,
                    "total_products": 0,
                    "total_variants": 0
                }
            }
        
        # Step 2: Get all products
        products_url = "https://api.holded.com/api/invoicing/v1/products"
        products_response = await client.get(products_url, headers=headers, timeout=30.0)
        
        if products_response.status_code != 200:
            raise Exception(f"Error al obtener productos: HTTP {products_response.status_code}")
        
        products = products_response.json()
        
        # Step 3: Get stock from each warehouse
        warehouse_stock_map = {}  # warehouse_id -> {product_id: stock_data}
        
        for warehouse in warehouses:
            warehouse_id = warehouse.get('id')
            if not warehouse_id:
                continue
            
            stock_url = f"https://api.holded.com/api/invoicing/v1/warehouses/{warehouse_id}/stock"
            stock_response = await client.get(stock_url, headers=headers, timeout=30.0)
            
            if stock_response.status_code == 200:
                stock_data = stock_response.json()
                warehouse_products = stock_data.get('warehouse', {}).get('products', [])
                
                # Map stock by product ID
                warehouse_stock_map[warehouse_id] = {}
                for stock_item in warehouse_products:
                    product_id = stock_item.get('product_id')
                    if product_id:
                        warehouse_stock_map[warehouse_id][product_id] = {
                            'stock': stock_item.get('stock', 0),
                            'variants': stock_item.get('variants', {})
                        }
        
        # Step 4: Consolidate data into table format
        products_list = []
        total_products = 0
        total_variants = 0
        
        for product in products:
            product_id = product.get('id')
            product_name = product.get('name', 'N/A')
            product_sku = product.get('sku', '')
            
            # Add main product if it has SKU
            if product_sku:
                stock_by_warehouse = {}
                
                for warehouse in warehouses:
                    warehouse_id = warehouse.get('id')
                    stock_info = warehouse_stock_map.get(warehouse_id, {}).get(product_id, {})
                    stock_by_warehouse[warehouse_id] = stock_info.get('stock', 0)
                
                products_list.append({
                    'sku': product_sku,
                    'name': product_name,
                    'type': 'principal',
                    'stock_by_warehouse': stock_by_warehouse
                })
                total_products += 1
            
            # Add variants if they exist
            variants = product.get('variants', [])
            for variant in variants:
                variant_id = variant.get('id')
                variant_sku = variant.get('sku', '')
                variant_name = variant.get('name', '')
                
                if variant_sku:
                    stock_by_warehouse = {}
                    
                    for warehouse in warehouses:
                        warehouse_id = warehouse.get('id')
                        stock_info = warehouse_stock_map.get(warehouse_id, {}).get(product_id, {})
                        variants_stock = stock_info.get('variants', {})
                        stock_by_warehouse[warehouse_id] = variants_stock.get(variant_id, 0)
                    
                    full_name = f"{product_name} - {variant_name}" if variant_name else product_name
                    
                    products_list.append({
                        'sku': variant_sku,
                        'name': full_name,
                        'type': 'variante',
                        'stock_by_warehouse': stock_by_warehouse
                    })
                    total_variants += 1
        
        warehouses_list = [
            {
                'id': wh.get('id'),
                'name': wh.get('name', 'Sin nombre')
            }
            for wh in warehouses
        ]
        
        return {
            "status": "success",
            "warehouses": warehouses_list,
            "products": products_list,
            "summary": {
                "total_warehouses": len(warehouses),
                "total_products": total_products,
                "total_variants": total_variants
            }
        }

async def update_stock_by_sku(request: StockUpdateRequest):
    if not settings.HOLDED_API_KEY:
        raise Exception("API key de Holded no configurada")
    
    async with httpx.AsyncClient() as client:
        headers = {
            "key": settings.HOLDED_API_KEY,
            "accept": "application/json",
            "content-type": "application/json"
        }
        
        # Step 1: Get all products to find the one with the given SKU
        products_url = "https://api.holded.com/api/invoicing/v1/products"
        products_response = await client.get(products_url, headers=headers, timeout=30.0)
        
        if products_response.status_code != 200:
            raise Exception(f"Error al obtener productos de Holded: HTTP {products_response.status_code}")
        
        products = products_response.json()
        
        # Find product or variant by SKU
        product_found = None
        product_id = None
        product_name = None
        is_variant = False
        variant_id = None
        
        for product in products:
            if product.get('sku') == request.sku:
                product_found = product
                product_id = product['id']
                product_name = product.get('name', 'N/A')
                is_variant = False
                break
            
            variants = product.get('variants', [])
            for variant in variants:
                if variant.get('sku') == request.sku:
                    product_found = product
                    product_id = product['id']
                    variant_id = variant['id']
                    product_name = f"{product.get('name', 'N/A')} - {variant.get('name', '')}"
                    is_variant = True
                    break
            
            if product_found:
                break
        
        if not product_found:
            raise Exception(f"No se encontró ningún producto o variante con SKU: {request.sku}")
        
        # Step 2: Validate that the warehouse exists
        warehouses_url = "https://api.holded.com/api/invoicing/v1/warehouses"
        warehouses_response = await client.get(warehouses_url, headers=headers, timeout=30.0)
        
        if warehouses_response.status_code != 200:
            raise Exception(f"Error al obtener almacenes: HTTP {warehouses_response.status_code}")
        
        warehouses = warehouses_response.json()
        warehouse_found = None
        
        for warehouse in warehouses:
            if warehouse.get('id') == request.warehouse_id:
                warehouse_found = warehouse
                break
        
        if not warehouse_found:
            raise Exception(f"No se encontró el almacén con ID: {request.warehouse_id}")
        
        # Step 3: Get current stock from warehouse
        stock_url = f"https://api.holded.com/api/invoicing/v1/warehouses/{request.warehouse_id}/stock"
        stock_response = await client.get(stock_url, headers=headers, timeout=30.0)
        
        current_stock = None
        if stock_response.status_code == 200:
            stock_data = stock_response.json()
            warehouse_products = stock_data.get('warehouse', {}).get('products', [])
            
            for stock_item in warehouse_products:
                if stock_item.get('product_id') == product_id:
                    if is_variant and variant_id:
                        variants_stock = stock_item.get('variants', {})
                        current_stock = variants_stock.get(variant_id, 0)
                    else:
                        current_stock = stock_item.get('stock', 0)
                    break
        
        if current_stock is None:
            current_stock = 0
        
        item_id = variant_id if is_variant else product_id
        
        stock_payload = {
            "stock": {
                request.warehouse_id: {
                    item_id: request.stock_adjustment
                }
            }
        }
        
        if request.description:
            stock_payload["desc"] = request.description
        
        response_data = {
            "status": "dry_run" if request.dry_run else "success",
            "product_info": {
                "sku": request.sku,
                "product_id": product_id,
                "product_name": product_name,
                "is_variant": is_variant,
                "variant_id": variant_id if is_variant else None
            },
            "warehouse_info": {
                "warehouse_id": request.warehouse_id,
                "warehouse_name": warehouse_found.get('name', 'N/A')
            },
            "stock_update": {
                "current_stock": current_stock,
                "stock_adjustment": request.stock_adjustment,
                "new_stock": current_stock + request.stock_adjustment,
                "description": request.description if request.description else None
            }
        }
        
        if request.dry_run:
            response_data["message"] = "Simulación exitosa - No se realizó ninguna actualización real"
            response_data["api_call"] = {
                "method": "PUT",
                "url": f"https://api.holded.com/api/invoicing/v1/products/{product_id}/stock",
                "payload": stock_payload
            }
        else:
            update_url = f"https://api.holded.com/api/invoicing/v1/products/{product_id}/stock"
            
            update_response = await client.put(
                update_url,
                headers=headers,
                json=stock_payload,
                timeout=30.0
            )
            
            if update_response.status_code == 200:
                response_data["message"] = "Stock actualizado exitosamente"
                response_data["holded_response"] = update_response.json()
            elif update_response.status_code == 204:
                response_data["message"] = "Stock actualizado exitosamente"
            else:
                raise Exception(f"Error al actualizar stock en Holded: HTTP {update_response.status_code} - {update_response.text}")
        
        return response_data

async def update_stock_from_gcs(request: StockUpdateFromGCSRequest):
    start_time = datetime.datetime.now(timezone.utc)
    log_data = {
        "timestamp_start": start_time.isoformat(),
        "input_uri": request.gs_uri,
        "dry_run": request.dry_run,
        "status": "started",
        "results": None,
        "error": None
    }

    async def upload_log(data: dict, bucket_name: str):
        try:
            log_client = get_gcs_client()
            log_bucket = log_client.bucket(bucket_name)
            
            timestamp = datetime.datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            log_filename = f"logs/stock_update_log_{timestamp}.json"
            log_blob = log_bucket.blob(log_filename)
            
            log_blob.upload_from_string(
                json.dumps(data, indent=2, default=str),
                content_type="application/json"
            )
            print(f"Log uploaded to gs://{bucket_name}/{log_filename}")
        except Exception as e:
            print(f"Failed to upload log: {str(e)}")

    try:
        if not settings.HOLDED_API_KEY:
            raise Exception("API key de Holded no configurada")
        
        # [NEW] Capture Database Snapshot
        try:
            snapshot = await get_stock_by_warehouse()
            log_data["database_snapshot"] = snapshot
        except Exception as snapshot_error:
            log_data["database_snapshot_error"] = str(snapshot_error)
            print(f"Failed to capture database snapshot: {snapshot_error}")

        if not request.gs_uri.startswith("gs://"):
            raise Exception("La URI debe comenzar con gs://")
        
        parts = request.gs_uri[5:].split("/", 1)
        if len(parts) != 2:
                raise Exception("URI inválida. Formato: gs://bucket/path/file.csv")
        
        bucket_name = parts[0]
        blob_name = parts[1]
        
        gcs = get_gcs_client()
        bucket = gcs.bucket(bucket_name)
        blob_name = blob_name.replace("%20", " ")
        blob = bucket.blob(blob_name)
        
        if not blob.exists():
                raise Exception(f"Archivo no encontrado en GCS: {request.gs_uri}")
                
        content_bytes = blob.download_as_bytes()
        
        try:
            df = pd.read_csv(io.BytesIO(content_bytes), sep=";", encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(content_bytes), sep=";", encoding='latin-1')
        
        required_cols = ["TERMINAL", "C.BARRAS ARTICULO", "UNIDADES"]
        for col in required_cols:
            if col not in df.columns:
                raise Exception(f"Columna faltante en CSV: {col}")
                
        async with httpx.AsyncClient() as client:
            headers = {
                "key": settings.HOLDED_API_KEY,
                "accept": "application/json",
                "content-type": "application/json"
            }
            
            warehouses_resp = await client.get("https://api.holded.com/api/invoicing/v1/warehouses", headers=headers, timeout=30.0)
            if warehouses_resp.status_code != 200:
                raise Exception(f"Error al obtener almacenes: {warehouses_resp.status_code}")
            
            warehouses = warehouses_resp.json()
            
            warehouse_map = {}
            for w in warehouses:
                name_norm = w.get('name', '').upper().strip()
                warehouse_map[name_norm] = w['id']
                warehouse_map[w['id']] = w['id']
            
            products_resp = await client.get("https://api.holded.com/api/invoicing/v1/products", headers=headers, timeout=60.0)
                
            if products_resp.status_code != 200:
                raise Exception(f"Error al obtener productos: {products_resp.status_code}")
                
            products = products_resp.json()
            
            product_map = {}
            for p in products:
                if p.get('sku'):
                    product_map[str(p['sku']).strip()] = {
                        'id': p['id'],
                        'name': p.get('name', ''),
                        'is_variant': False,
                        'variant_id': None
                    }
                
                for v in p.get('variants', []):
                    if v.get('sku'):
                        product_map[str(v['sku']).strip()] = {
                            'id': p['id'],
                            'name': f"{p.get('name','')} - {v.get('name','')}",
                            'is_variant': True,
                            'variant_id': v['id']
                        }

            terminals_in_csv = df["TERMINAL"].unique()
            used_warehouse_ids = set()
            
            def resolve_warehouse_id(term_name):
                term_upper = str(term_name).upper().strip()
                w_id = warehouse_map.get(term_upper)
                if not w_id:
                    if "MURCIA" in term_upper: w_id = warehouse_map.get("TIENDA MURCIA")
                    elif "SALAMANCA" in term_upper: w_id = warehouse_map.get("TIENDA SALAMANCA")
                    elif "CACERES" in term_upper or "CÁCERES" in term_upper:
                        for key, val in warehouse_map.items():
                                if "CÁCERES" in key and "TIENDA" in key: return val
                        return "685036750bb898af5e05dd11"
                return w_id

            for term in terminals_in_csv:
                w_id = resolve_warehouse_id(term)
                if w_id:
                    used_warehouse_ids.add(w_id)
            
            stock_data_map = {}
            
            for w_id in used_warehouse_ids:
                stock_url = f"https://api.holded.com/api/invoicing/v1/warehouses/{w_id}/stock"
                s_resp = await client.get(stock_url, headers=headers, timeout=30.0)
                if s_resp.status_code == 200:
                    data = s_resp.json()
                    w_prods = data.get("warehouse", {}).get("products", [])
                    stock_data_map[w_id] = {}
                    for item in w_prods:
                        pid = item.get("product_id")
                        if pid:
                            stock_data_map[w_id][pid] = {
                                "stock": item.get("stock", 0),
                                "variants": item.get("variants", {})
                            }

            results = {
                "processed": 0,
                "updated": 0,
                "errors": [],
                "updates": []
            }
            
            for index, row in df.iterrows():
                results["processed"] += 1
                
                try:
                    terminal = str(row["TERMINAL"]).strip()
                    sku = str(row["C.BARRAS ARTICULO"]).strip()
                    
                    csv_product = "Unknown"
                    for col in df.columns:
                        normalized = str(col).upper().replace("Í", "I").replace("í", "I").strip()
                        if normalized == "ARTICULO" or normalized == "ARTCULO":
                                csv_product = str(row[col]).strip()
                                break
                                
                    units_val = str(row["UNIDADES"]).replace(',', '.')
                    if not units_val or units_val.lower() == 'nan':
                            continue
                    units = float(units_val)
                except Exception as e:
                    results["errors"].append({
                        "row": index,
                        "error": f"Error parsing data: {str(e)}",
                        "sku": sku if 'sku' in locals() else "Unknown",
                        "product": csv_product if 'csv_product' in locals() else "Unknown",
                        "units": units if 'units' in locals() else None,
                        "terminal": terminal if 'terminal' in locals() else "Unknown"
                    })
                    continue
                
                w_id = resolve_warehouse_id(terminal)
                if not w_id:
                    results["errors"].append({
                        "row": index,
                        "error": f"Almacén '{terminal}' no encontrado",
                        "sku": sku,
                        "product": csv_product,
                        "units": units,
                        "terminal": terminal
                    })
                    continue
                
                p_info = product_map.get(sku)
                if not p_info:
                    results["errors"].append({
                        "row": index,
                        "error": f"SKU '{sku}' no encontrado",
                        "sku": sku,
                        "product": csv_product,
                        "units": units,
                        "terminal": terminal
                    })
                    continue
                    
                adjustment = -1 * units
                
                current_stock = 0
                main_pid = p_info['id']
                is_variant = p_info['is_variant']
                var_id = p_info['variant_id']
                
                if w_id in stock_data_map and main_pid in stock_data_map[w_id]:
                    item_stock_data = stock_data_map[w_id][main_pid]
                    if is_variant and var_id:
                        variants_data = item_stock_data.get("variants", {})
                        if variants_data and isinstance(variants_data, dict):
                            current_stock = variants_data.get(var_id, 0)
                        else:
                                current_stock = 0
                    else:
                        current_stock = item_stock_data.get("stock", 0)
                
                new_stock = current_stock + adjustment
                
                item_id = var_id if is_variant else main_pid
                
                stock_payload = {
                    "stock": {
                        w_id: {
                            item_id: adjustment
                        }
                    }
                }
                
                update_info = {
                    "row": index,
                    "sku": sku,
                    "product": p_info['name'],
                    "warehouse": terminal,
                    "warehouse_id": w_id,
                    "units_sold": units,
                    "adjustment": adjustment,
                    "current_stock": current_stock,
                    "new_stock": new_stock
                }
                
                if request.dry_run:
                    update_info["status"] = "simulated"
                    results["updates"].append(update_info)
                else:
                    update_url = f"https://api.holded.com/api/invoicing/v1/products/{main_pid}/stock"
                    upd_resp = await client.put(update_url, headers=headers, json=stock_payload, timeout=10.0)
                    
                    if upd_resp.status_code in [200, 204]:
                        update_info["status"] = "success"
                        results["updated"] += 1
                        results["updates"].append(update_info)
                    else:
                        update_info["status"] = "error"
                        update_info["error_detail"] = f"HTTP {upd_resp.status_code} - {upd_resp.text}"
                        results["errors"].append({
                            "row": index, 
                            "error": f"API Error: {upd_resp.text}", 
                            "sku": sku, 
                            "product": p_info['name'],
                            "units": units,
                            "terminal": terminal
                        })

        log_data["results"] = results
        log_data["status"] = "success"
        return results
        
    except Exception as e:
        log_data["status"] = "error"
        log_data["error"] = str(e)
        raise e
        
    finally:
        end_time = datetime.datetime.now(timezone.utc)
        log_data["timestamp_end"] = end_time.isoformat()
        log_data["duration_seconds"] = (end_time - start_time).total_seconds()
        
        # Determine bucket name for logs (same as input file if possible)
        log_bucket_name = settings.GCS_BUCKET_NAME
        if request.gs_uri.startswith("gs://"):
            try:
                parts = request.gs_uri[5:].split("/", 1)
                if len(parts) >= 1:
                    log_bucket_name = parts[0]
            except:
                pass
                
        await upload_log(log_data, log_bucket_name)

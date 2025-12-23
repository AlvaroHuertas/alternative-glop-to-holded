
import base64
import json
import tempfile
import os
from google.cloud import storage
from app.core.config import settings

def get_gcs_client():
    """Initialize and return a Google Cloud Storage client using base64-encoded credentials"""
    if not settings.GCS_CREDENTIALS_BASE64:
        raise Exception("GCS credentials not configured")
    
    try:
        # Decode base64 credentials
        credentials_json = base64.b64decode(settings.GCS_CREDENTIALS_BASE64).decode('utf-8')
        credentials_dict = json.loads(credentials_json)
        
        # Create a temporary file for credentials
        # Note: In a production environment, it's better to pass credentials dict directly 
        # using service_account.Credentials.from_service_account_info(credentials_dict)
        # However, preserving existing logic for now.
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(credentials_dict, temp_file)
            temp_file_path = temp_file.name
        
        # Initialize client with credentials
        client = storage.Client.from_service_account_json(temp_file_path)
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        return client
    except Exception as e:
        raise Exception(f"Error initializing GCS client: {str(e)}")

def get_bucket():
    client = get_gcs_client()
    return client.bucket(settings.GCS_BUCKET_NAME)

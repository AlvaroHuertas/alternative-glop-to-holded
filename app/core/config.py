
import os
from dotenv import load_dotenv

# Load environment variables (try .env.local first, then .env)
load_dotenv(".env.local")
load_dotenv()

class Settings:
    HOLDED_API_KEY = os.getenv("HOLDED_API_KEY", "")
    HOLDED_BASE_URL = os.getenv("HOLDED_BASE_URL", "https://api.holded.com/api/invoicing/v1/products")
    GCS_CREDENTIALS_BASE64 = os.getenv("GCS_CREDENTIALS_BASE64", "")
    GCS_BUCKET_NAME = "alternativecbd-glop-reports"

settings = Settings()

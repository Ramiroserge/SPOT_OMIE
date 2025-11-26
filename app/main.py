import os
from dotenv import load_dotenv
from app.product_sync import sync_products
import logging

logging.basicConfig(level=logging.INFO)
load_dotenv()

SPOT_ACCESS_KEY = os.getenv("SPOT_ACCESS_KEY")
OMIE_APP_KEY = os.getenv("OMIE_APP_KEY")
OMIE_APP_SECRET = os.getenv("OMIE_APP_SECRET")

# ⚠️ Real sync: no preview, no dry-run
sync_products(
    spot_key=SPOT_ACCESS_KEY,
    omie_app_key=OMIE_APP_KEY,
    omie_app_secret=OMIE_APP_SECRET,
    dry_run=False,
    preview_count=None
)

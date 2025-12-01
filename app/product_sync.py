import json
import time
import pandas as pd
from spot_client import SpotClient
from omie_client import OmieClient
from spot_mapper import map_spot_to_omie
import logging

logger = logging.getLogger(__name__)


def sync_products(spot_key, omie_app_key, omie_app_secret, dry_run=False, preview_count=None):
    spot_client = SpotClient(access_key=spot_key)
    omie_client = OmieClient(app_key=omie_app_key, app_secret=omie_app_secret)
    skipped_products = []



    products = spot_client.fetch_products().get("Products", [])
    prices = spot_client.fetch_price().get("OptionalsPrice", [])
    logger.info("\U0001F4E6 Fetching products from SPOT...")
    logger.info(f"✅ Fetched {len(products)} products from SPOT.")
    if products:
        pd.DataFrame(products).to_csv("produtos_spot.csv", index=False)
    if prices:
        pd.DataFrame(prices).to_csv("prices_spot.csv", index=False)
    if preview_count is not None:
        products = products[:preview_count]

    logger.info("\U0001F4E6 Fetching products from OMIE...")
    existing_products = omie_client.list_products()
    existing_codes = set(p.get("codigo_produto_integracao") for p in existing_products if p.get("codigo_produto_integracao"))
    logger.info("✅ OMIE existing codes (first 10): %s", list(existing_codes)[:10])

    logger.info("\U0001F6E0️ Processing %d product%s from SPOT to OMIE...", len(products), "s" if len(products) != 1 else "")

    for product in products:
        code = product.get("ProdReference")
        if not code:
            logger.warning("❌ Skipping product with no ProdReference")
            continue

        if code in existing_codes:
            logger.info("⏭️ Skipping %s — already exists in OMIE.", code)
            continue

        omie_payload = map_spot_to_omie(product)
        logger.info("\U0001F9BE OMIE Payload:\n%s\n", json.dumps(omie_payload, indent=2, ensure_ascii=False))

        if not dry_run:
            try:
                response = omie_client.insert_product(omie_payload)
                logger.info("📬 OMIE Response: %s", response)

                if isinstance(response, dict) and "faultcode" in response:
                    fault_msg = response.get("faultstring", "")
                    if "NCM não cadastrada" in fault_msg:
                        logger.warning("⚠️ Skipping due to missing NCM: %s", code)
                        skipped_products.append(omie_payload)
                        continue

                    logger.error("🚫 OMIE Error (%s): %s", response["faultcode"], fault_msg)
                    logger.warning("🛑 Stopping sync due to fatal OMIE error.")
                    break
            except Exception as e:
                logger.exception("❌ Unexpected exception while inserting product: %s", e)

        time.sleep(1)

    if skipped_products:
        pd.DataFrame(skipped_products).to_csv("skipped_products.csv", index=False)
        logger.info("⚠️ Saved skipped products to skipped_products.csv")

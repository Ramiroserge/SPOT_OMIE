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
    
    # Tracking lists for final summary
    inserted_products = []      # Successfully inserted
    skipped_existing = []       # Already exist in OMIE
    skipped_no_reference = []   # Missing ProdReference
    error_products = []         # Products with errors (NCM, etc.)



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

    fatal_error = False
    for product in products:
        code = product.get("ProdReference")
        name = product.get("ProdName", "Unknown")
        
        if not code:
            logger.warning("❌ Skipping product with no ProdReference: %s", name)
            skipped_no_reference.append({"name": name, "reason": "No ProdReference"})
            continue

        if code in existing_codes:
            logger.info("⏭️ Skipping %s — already exists in OMIE.", code)
            skipped_existing.append({"code": code, "name": name})
            continue

        omie_payload = map_spot_to_omie(product)
        logger.info("\U0001F9BE OMIE Payload:\n%s\n", json.dumps(omie_payload, indent=2, ensure_ascii=False))

        if not dry_run:
            try:
                response = omie_client.insert_product(omie_payload)
                logger.info("📬 OMIE Response: %s", response)

                if isinstance(response, dict) and "faultcode" in response:
                    fault_msg = response.get("faultstring", "")
                    fault_code = response.get("faultcode", "")
                    
                    error_products.append({
                        "code": code,
                        "name": name,
                        "error_code": fault_code,
                        "error_message": fault_msg
                    })
                    
                    if "NCM não cadastrada" in fault_msg:
                        logger.warning("⚠️ Skipping due to missing NCM: %s", code)
                        continue

                    logger.error("🚫 OMIE Error (%s): %s", fault_code, fault_msg)
                    logger.warning("🛑 Stopping sync due to fatal OMIE error.")
                    fatal_error = True
                    break
                else:
                    # Successfully inserted
                    inserted_products.append({
                        "code": code,
                        "name": name,
                        "omie_codigo": response.get("codigo_produto") if response else None
                    })
                    
            except Exception as e:
                logger.exception("❌ Unexpected exception while inserting product: %s", e)
                error_products.append({
                    "code": code,
                    "name": name,
                    "error_code": "EXCEPTION",
                    "error_message": str(e)
                })

        time.sleep(1)

    # === FINAL EXECUTION SUMMARY ===
    _log_execution_summary(
        products=products,
        inserted=inserted_products,
        skipped_existing=skipped_existing,
        skipped_no_ref=skipped_no_reference,
        errors=error_products,
        dry_run=dry_run,
        fatal_error=fatal_error
    )
    
    # Save CSVs for reference
    if error_products:
        pd.DataFrame(error_products).to_csv("error_products.csv", index=False)
        logger.info("📄 Saved error products to error_products.csv")
    
    if inserted_products:
        pd.DataFrame(inserted_products).to_csv("inserted_products.csv", index=False)
        logger.info("📄 Saved inserted products to inserted_products.csv")


def _log_execution_summary(products, inserted, skipped_existing, skipped_no_ref, errors, dry_run, fatal_error):
    """Logs a comprehensive summary of the sync execution."""
    total = len(products)
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("📊 EXECUTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total products from SPOT:      {total}")
    logger.info(f"Successfully inserted:         {len(inserted)}")
    logger.info(f"Skipped (already in OMIE):     {len(skipped_existing)}")
    logger.info(f"Skipped (no ProdReference):    {len(skipped_no_ref)}")
    logger.info(f"Errors:                        {len(errors)}")
    if dry_run:
        logger.info(f"Mode:                          DRY RUN (no changes made)")
    if fatal_error:
        logger.info(f"Status:                        ⚠️ STOPPED DUE TO FATAL ERROR")
    logger.info("=" * 60)
    
    # List successfully inserted products
    if inserted:
        logger.info("")
        logger.info("✅ PRODUCTS INSERTED SUCCESSFULLY:")
        logger.info("-" * 40)
        for p in inserted:
            logger.info(f"  • [{p['code']}] {p['name']}")
    
    # List products with errors
    if errors:
        logger.info("")
        logger.info("❌ PRODUCTS WITH ERRORS:")
        logger.info("-" * 40)
        for p in errors:
            logger.info(f"  • [{p['code']}] {p['name']}")
            logger.info(f"    Error: {p['error_code']} - {p['error_message']}")
    
    # List skipped products (already exist)
    if skipped_existing:
        logger.info("")
        logger.info("⏭️ PRODUCTS SKIPPED (already in OMIE):")
        logger.info("-" * 40)
        for p in skipped_existing:
            logger.info(f"  • [{p['code']}] {p['name']}")
    
    # List products without reference
    if skipped_no_ref:
        logger.info("")
        logger.info("⚠️ PRODUCTS SKIPPED (no ProdReference):")
        logger.info("-" * 40)
        for p in skipped_no_ref:
            logger.info(f"  • {p['name']} - {p['reason']}")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("🏁 SYNC COMPLETED")
    logger.info("=" * 60)

from spot_client import SpotClient
from typing import List, Dict, Any
import logging
import pandas as pd

logger = logging.getLogger(__name__)

# NCM correction mapping for incorrect codes from SPOT API
NCM_CORRECTIONS = {
    "96171000": "90251990",  # 9617.10.00 > 9025.19.90
    "9617.10.00": "9025.19.90",
    "96081099": "96081000",  # 9608.10.99 > 9608.10.00
    "9608.10.99": "9608.10.00",
    "9608109900": "96081000",  # Handle 10-digit version
}

def fix_ncm(ncm: str) -> str:
    """
    Corrects known incorrect NCM codes from SPOT API.
    Returns the corrected NCM or the original if no correction needed.
    """
    if not ncm:
        return ncm
    
    # Remove dots and normalize
    ncm_normalized = ncm.replace(".", "")
    
    # NCM should be 8 digits, truncate if longer
    if len(ncm_normalized) > 8:
        logger.warning(f"⚠️ NCM has {len(ncm_normalized)} digits, truncating to 8: {ncm_normalized}")
        ncm_normalized = ncm_normalized[:8]
    
    # Check if correction is needed (exact match)
    if ncm_normalized in NCM_CORRECTIONS:
        corrected = NCM_CORRECTIONS[ncm_normalized]
        logger.info(f"🔧 NCM correction: {ncm} → {corrected}")
        return corrected
    
    # Also check original with dots
    if ncm in NCM_CORRECTIONS:
        corrected = NCM_CORRECTIONS[ncm]
        logger.info(f"🔧 NCM correction: {ncm} → {corrected}")
        return corrected
    
    return ncm_normalized

def fetch_spot_products(spot: SpotClient) -> List[Dict[str, Any]]:
    response = spot.fetch_products()
    products = response.get("Products", [])

    logger.info(f"Fetched {len(products)} products from SPOT.")

    if not products:
        logger.warning("No products were returned from SPOT.")
        return []

    df = pd.DataFrame(products)
    df.to_csv("spot_products.csv", index=False)
    logger.info("Saved all products to spot_products.csv")

    return products

def map_spot_to_omie(spot_product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Maps a single SPOT product to the OMIE API format.
    Adjust this function based on actual field mappings.
    """
    integration_code = spot_product.get("ProdReference")

    cor = spot_product.get("Colors").strip()
    descricao = spot_product.get("Name")
    descr_detalhada = spot_product.get("Description")
    ncm_original = spot_product.get("Taric")
    ncm = fix_ncm(ncm_original)  # Apply NCM correction
    peso_bruto = round(spot_product.get("Weight", 0) / 1000, 3)
    desc_truncada = f"{descricao} - Cor: {cor} - Codigo: {integration_code}"
    return {
        "codigo": integration_code,
        "codigo_produto_integracao": integration_code,
        "descricao": desc_truncada[:120],
        "descr_detalhada": descr_detalhada,
        "ncm": ncm,
        "peso_bruto": peso_bruto,
        "unidade": "UN",
        "importado_api": "S"
    }

from spot_client import SpotClient
from typing import List, Dict, Any
import logging
import pandas as pd

logger = logging.getLogger(__name__)

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
    ncm = spot_product.get("Taric")
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

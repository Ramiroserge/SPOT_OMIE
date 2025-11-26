import requests
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class OmieClient:
    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.url = "https://app.omie.com.br/api/v1/geral/produtos/"

    def _build_headers(self) -> Dict[str, str]:
        return {"Content-Type": "application/json"}

    def _build_auth_payload(self) -> Dict[str, str]:
        return {"app_key": self.app_key, "app_secret": self.app_secret}

    def list_products(self, page: int = 1, page_size: int = 500) -> List[Dict[str, Any]]:
        """
        Lists products from OMIE in a paginated manner.
        """
        all_products = []

        while True:
            payload = {
                **self._build_auth_payload(),
                "call": "ListarProdutos",
                "param": [{
                    "pagina": page,
                    "registros_por_pagina": page_size,
                    "apenas_importado_api": "S",
                    "filtrar_apenas_omiepdv": "N"
                }]
            }

            try:
                response = requests.post(self.url, json=payload, headers=self._build_headers())
                response.raise_for_status()
                data = response.json()
                products = data.get("produto_servico_cadastro", [])

                if not products:
                    logging.warning(f"No products found on page {page}.")
                else:
                    logging.debug(f"Page {page} - First product: {products[0]}")
                    logging.debug(f"Page {page} - Number of products: {len(products)}")

                all_products.extend(products)

                if page >= data.get("total_de_paginas", 1):
                    break

                page += 1

            except requests.HTTPError as e:
                logging.error(f"OMIE error on ListarProdutos (page {page}): {e}")
                logging.error(f"OMIE response:\n{response.text}")
                logging.warning("Skipping remaining pages due to error on page {page}")
                break

        logging.info(f"Fetched {len(all_products)} products from OMIE.")
        return all_products
    def insert_product(self, product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Inserts a new product into OMIE, with detailed error logging.
        """
        payload = {
            **self._build_auth_payload(),
            "call": "IncluirProduto",
            "param": [product]
        }

        # 🔍 Log the outgoing payload
        import pprint
        logger.info("Sending product to OMIE:")
        pprint.pprint(payload)

        try:
            response = requests.post(self.url, json=payload, headers=self._build_headers())
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTPError while calling OMIE: {e}")
            logger.error(f"OMIE response body:\n{response.text}")
            raise

        result = response.json()

        if result.get("faultstring"):
            logger.error(f"OMIE application-level error: {result['faultstring']}")
            return None

        logger.info(f"Inserted product with integration code: {product.get('codigo_produto_integracao')}")
        return result
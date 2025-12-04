import requests
import logging
from typing import List, Dict, Any, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

# Retry configuration for transient network errors
RETRY_CONFIG = {
    "stop": stop_after_attempt(5),  # Max 5 attempts
    "wait": wait_exponential(multiplier=1, min=2, max=30),  # 2s, 4s, 8s, 16s, 30s
    "retry": retry_if_exception_type((
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.ChunkedEncodingError,
    )),
    "before_sleep": before_sleep_log(logger, logging.WARNING),
    "reraise": True,
}

class OmieClient:
    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.url = "https://app.omie.com.br/api/v1/geral/produtos/"

    def _build_headers(self) -> Dict[str, str]:
        return {"Content-Type": "application/json"}

    def _build_auth_payload(self) -> Dict[str, str]:
        return {"app_key": self.app_key, "app_secret": self.app_secret}

    @retry(**RETRY_CONFIG)
    def _make_request(self, payload: Dict[str, Any]) -> requests.Response:
        """
        Makes a POST request to OMIE API with automatic retry on transient failures.
        Retries up to 5 times with exponential backoff (2s, 4s, 8s, 16s, 30s).
        """
        response = requests.post(
            self.url,
            json=payload,
            headers=self._build_headers(),
            timeout=60  # 60 second timeout
        )
        return response

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
                response = self._make_request(payload)
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

            except requests.exceptions.ConnectionError as e:
                logging.error(f"Connection error on ListarProdutos (page {page}) after all retries: {e}")
                logging.warning(f"Skipping remaining pages due to connection error on page {page}")
                break
            except requests.HTTPError as e:
                logging.error(f"OMIE error on ListarProdutos (page {page}): {e}")
                logging.error(f"OMIE response:\n{response.text}")
                logging.warning(f"Skipping remaining pages due to error on page {page}")
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
            response = self._make_request(payload)
            
            # Parse JSON response first to check for OMIE application errors
            result = response.json()
            
            # Check if OMIE returned a fault (even with HTTP 500)
            if result.get("faultstring") or result.get("faultcode"):
                logger.warning(f"OMIE application error: {result.get('faultstring', 'Unknown error')}")
                return result  # Return the error dict so caller can handle it
            
            # Only raise for HTTP errors if it's not an OMIE fault response
            response.raise_for_status()
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error while calling OMIE after all retries: {e}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTPError while calling OMIE: {e}")
            logger.error(f"OMIE response body:\n{response.text}")
            raise
        except ValueError as e:
            # JSON parsing failed
            logger.error(f"Failed to parse OMIE response: {e}")
            logger.error(f"Response body:\n{response.text}")
            response.raise_for_status()
            raise

        logger.info(f"✅ Inserted product with integration code: {product.get('codigo_produto_integracao')}")
        return result
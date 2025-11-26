import requests
import logging
from typing import Optional, Dict, Any
import json


logger = logging.getLogger(__name__)

class SpotClient:
    def __init__(self, access_key: str, lang: str = "PT"):
        self.access_key = access_key
        self.lang = lang
        self.base_url = "http://ws.spotgifts.com.br/api/v1"
        self.session_token: Optional[str] = None

    def authenticate(self) -> None:
        """
        Authenticates using the access key and retrieves a session token.
        """
        url = f"{self.base_url}/authenticateclient?AccessKey={self.access_key}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data.get("ErrorCode") is not None:
            raise Exception(f"Authentication failed: {data['ErrorMessage']}")

        self.session_token = data.get("Token")
        logger.info("Authenticated successfully. Token obtained.")

    def validate_session(self) -> bool:
        """
        Validates the current session token.
        """
        if not self.session_token:
            logger.warning("No session token to validate.")
            return False

        url = f"{self.base_url}/validateSession?token={self.session_token}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        is_valid = data.get("Status") == 1
        if is_valid:
            logger.info("Session token is valid.")
        else:
            logger.warning("Session token is invalid.")

        return is_valid

    def fetch_products(self) -> Dict[str, Any]:
        """
        Fetches products using the current valid session token.
        If no token or invalid, re-authenticates first.
        """

        logger.info("Authenticating to obtain new session token...")
        self.authenticate()
        self.validate_session()

        url = f"{self.base_url}/products"
        params = {"token": self.session_token, "lang": self.lang}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def fetch_price(self) -> Dict[str, Any]:
        logger.info("Authenticating to obtain new session token...")
        self.authenticate()
        self.validate_session()

        url = f"{self.base_url}/optionalsPrice"
        params = {"token": self.session_token, "lang": self.lang}
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        logger.debug("📊 SPOT price data: %s", json.dumps(data, indent=2, ensure_ascii=False))
        return data

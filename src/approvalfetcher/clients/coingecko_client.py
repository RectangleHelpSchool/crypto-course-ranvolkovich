import logging
import asyncio
from typing import Optional
from .rest_client import RestClient
from ..utils.config import get_settings
from ..utils.constants import COINGECKO_TOKEN_BY_CONTRACT_PATH, TOKEN_PRICE_CURRENCY

logger = logging.getLogger(__name__)


class CoinGeckoClient(RestClient):

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.settings = get_settings()

        if api_key is None:
            api_key = self.settings.coingecko_api_key if self.settings.coingecko_api_key else None

        super().__init__(base_url=self.settings.coingecko_base_url, api_key=api_key)

    async def __aenter__(self) -> "CoinGeckoClient":
        await super().__aenter__()
        return self

    async def _get_token_price_by_address(self, contract_address: str) -> Optional[float]:
        headers = {}
        if self.api_key:
            headers["x-cg-demo-api-key"] = self.api_key

        path = COINGECKO_TOKEN_BY_CONTRACT_PATH.format(address=contract_address.lower())
        data = await self.get(path, headers=headers)

        if not data:
            return None

        price = data.get("market_data", {}).get("current_price", {}).get(TOKEN_PRICE_CURRENCY)
        return price

    async def get_multiple_prices(self, contract_addresses: list[str]) -> dict[str, Optional[float]]:
        tasks = [
            self._get_token_price_by_address(address)
            for address in contract_addresses
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        prices = {}
        for address, result in zip(contract_addresses, results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to fetch price for {address}: {result}")
                prices[address.lower()] = None
            else:
                prices[address.lower()] = result

        return prices

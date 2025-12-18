import logging
from typing import Optional
from ..clients.coingecko_client import CoinGeckoClient

logger = logging.getLogger(__name__)


class PriceService:

    def __init__(self, client: CoinGeckoClient):
        self.client = client

    async def fetch_prices(self, token_addresses: list[str]) -> dict[str, Optional[float]]:
        if not token_addresses:
            return {}

        unique_addresses = list(set(token_addresses))
        return await self.client.get_multiple_prices(unique_addresses)

import logging
from typing import Any, Optional
import aiohttp

logger = logging.getLogger(__name__)


class RestClient:

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "RestClient":
        self.session = aiohttp.ClientSession()
        logger.info(f"REST client connected to {self.base_url}")
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.session:
            await self.session.close()
        logger.info("REST client disconnected")

    async def get(self, path: str, headers: Optional[dict] = None, timeout: int = 10) -> Optional[dict]:
        if not self.session:
            raise RuntimeError("Client not initialized")

        url = f"{self.base_url}{path}"
        headers = headers or {}

        try:
            async with self.session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                if response.status == 404:
                    return None

                if response.status != 200:
                    logger.warning(f"API error: {response.status} for {url}")
                    return None

                return await response.json()

        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

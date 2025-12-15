import asyncio
import logging
from web3 import AsyncWeb3, AsyncHTTPProvider
from ..utils.config import get_settings
from ..utils.eth_utils import pad_address
from ..utils.constants import APPROVAL_EVENT_SIGNATURE, ERC20_ABI

logger = logging.getLogger(__name__)


class Web3Client:

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.infura_api_key
        self.endpoint = f"{self.settings.infura_endpoint}{self.api_key}"

        provider = AsyncHTTPProvider(self.endpoint)
        self.w3 = AsyncWeb3(provider)

    async def __aenter__(self):
        try:
            is_connected = await self.w3.is_connected()
            if not is_connected:
                raise ConnectionError("Failed to connect to Infura endpoint")

            logger.info("Successfully connected to Ethereum via Infura")
            return self
        except Exception:
            logger.exception("Failed to initialize Web3 client")
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.w3 and self.w3.provider:
            await self.w3.provider.disconnect()
        logger.info("Web3 client disconnected")

    async def get_latest_block(self) -> int:
        block_number = await self.w3.eth.block_number
        logger.debug(f"Latest block number: {block_number}")
        return block_number

    async def get_logs(
        self,
        from_block: int | str,
        to_block: int | str,
        topics: list[str]
    ) -> list[dict]:
        filter_params = {
            'fromBlock': from_block,
            'toBlock': to_block,
            'topics': topics
        }

        logger.debug(f"Fetching logs from block {from_block} to {to_block}")
        logs = await self.w3.eth.get_logs(filter_params)
        logger.debug(f"Retrieved {len(logs)} logs")
        return [dict(log) for log in logs]

    async def get_all_approval_logs(self, owner_address: str) -> list[dict]:
        logger.info(f"Fetching all approval events for {owner_address}")

        padded_owner = pad_address(owner_address)

        topics = [
            APPROVAL_EVENT_SIGNATURE,
            padded_owner,
        ]

        try:
            logger.info("Attempting to fetch all approvals in single query (blocks 0 to latest)...")
            logs = await self.get_logs(0, 'latest', topics)
            logger.info(f"✓ Successfully fetched {len(logs)} approval events in single query!")
            return logs

        except Exception:
            logger.exception("Unexpected error during full range query")
            raise

    async def get_token_symbol(self, token_address: str) -> str:
        try:
            contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
            symbol = await contract.functions.symbol().call()
            return symbol.strip() if symbol else "UnknownERC20"
        except Exception as e:
            logger.debug(f"Failed to fetch symbol for token {token_address}: {e}")
            return "UnknownERC20"

    async def get_token_name(self, token_address: str) -> str:
        try:
            contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
            name = await contract.functions.name().call()
            return name.strip() if name else "UnknownERC20"
        except Exception as e:
            logger.debug(f"Failed to fetch name for token {token_address}: {e}")
            return "UnknownERC20"

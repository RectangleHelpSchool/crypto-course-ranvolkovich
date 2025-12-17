import logging
from typing import Any, cast
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.types import FilterParams, LogReceipt, BlockIdentifier
from eth_typing import ChecksumAddress
from ..utils.config import get_settings
from ..utils.eth_utils import pad_address
from ..utils.constants import APPROVAL_EVENT_SIGNATURE, ERC20_ABI

logger = logging.getLogger(__name__)


class Web3Client:

    def __init__(self) -> None:
        self.settings = get_settings()
        self.api_key = self.settings.infura_api_key
        self.endpoint = f"{self.settings.infura_endpoint}{self.api_key}"

        provider = AsyncHTTPProvider(self.endpoint)
        self.w3 = AsyncWeb3(provider)

    async def __aenter__(self) -> "Web3Client":
        try:
            is_connected = await self.w3.is_connected()
            if not is_connected:
                raise ConnectionError("Failed to connect to Infura endpoint")

            logger.info("Successfully connected to Ethereum via Infura")
            return self
        except Exception:
            logger.exception("Failed to initialize Web3 client")
            raise

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.w3 and self.w3.provider:
            await self.w3.provider.disconnect()
        logger.info("Web3 client disconnected")

    async def get_latest_block(self) -> int:
        block_number = await self.w3.eth.block_number
        logger.debug(f"Latest block number: {block_number}")
        return block_number

    async def _get_logs(
        self,
        from_block: BlockIdentifier,
        to_block: BlockIdentifier,
        topics: list[str]
    ) -> list[LogReceipt]:
        filter_params: FilterParams = {
            'fromBlock': from_block,
            'toBlock': to_block,
            'topics': topics
        }

        from_str = from_block.hex() if isinstance(from_block, bytes) else str(from_block)
        to_str = to_block.hex() if isinstance(to_block, bytes) else str(to_block)
        logger.debug(f"Fetching logs from block {from_str} to {to_str}")
        logs = await self.w3.eth.get_logs(filter_params)
        logger.debug(f"Retrieved {len(logs)} logs")
        return list(logs)

    async def get_all_approval_logs(self, owner_address: str) -> list[LogReceipt]:
        logger.info(f"Fetching all approval events for {owner_address}")

        padded_owner = pad_address(owner_address)

        topics = [
            APPROVAL_EVENT_SIGNATURE,
            padded_owner,
        ]

        try:
            logger.info("Attempting to fetch all approvals in single query (blocks 0 to latest)...")
            logs = await self._get_logs(0, 'latest', topics)
            logger.info(f"✓ Successfully fetched {len(logs)} approval events in single query!")
            return logs

        except Exception:
            logger.exception("Unexpected error during full range query")
            raise

    async def get_token_symbol(self, token_address: str) -> str:
        try:
            contract = self.w3.eth.contract(
                address=cast(ChecksumAddress, token_address),
                abi=ERC20_ABI
            )
            symbol = await contract.functions.symbol().call()
            return symbol.strip() if symbol else "UnknownERC20"
        except Exception as e:
            logger.debug(f"Failed to fetch symbol for token {token_address}: {e}")
            return "UnknownERC20"

    async def get_token_name(self, token_address: str) -> str:
        try:
            contract = self.w3.eth.contract(
                address=cast(ChecksumAddress, token_address),
                abi=ERC20_ABI
            )
            name = await contract.functions.name().call()
            return name.strip() if name else "UnknownERC20"
        except Exception as e:
            logger.debug(f"Failed to fetch name for token {token_address}: {e}")
            return "UnknownERC20"

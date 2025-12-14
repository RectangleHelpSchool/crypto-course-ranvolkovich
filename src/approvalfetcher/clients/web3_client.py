import asyncio
import logging
from typing import Optional
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.exceptions import Web3Exception
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from ..utils.config import get_settings
from ..utils.eth_utils import pad_address

logger = logging.getLogger(__name__)


class Web3Client:
    """Async Web3 client for Ethereum blockchain with retry logic."""

    # ERC-20 Approval event signature: Approval(address indexed owner, address indexed spender, uint256 value)
    APPROVAL_EVENT_SIGNATURE = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"

    def __init__(self, infura_api_key: Optional[str] = None):
        """Initialize Web3 client with Infura endpoint."""
        self.settings = get_settings()
        self.api_key = infura_api_key or self.settings.infura_api_key
        self.endpoint = f"{self.settings.infura_endpoint}{self.api_key}"
        self.w3: Optional[AsyncWeb3] = None

    async def __aenter__(self):
        """Async context manager entry - initialize Web3 connection."""
        try:
            provider = AsyncHTTPProvider(self.endpoint)
            self.w3 = AsyncWeb3(provider)

            # Test connection
            is_connected = await self.w3.is_connected()
            if not is_connected:
                raise ConnectionError("Failed to connect to Infura endpoint")

            logger.info("Successfully connected to Ethereum via Infura")
            return self
        except Exception as e:
            logger.error(f"Failed to initialize Web3 client: {e}")
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup resources."""
        if self.w3 and self.w3.provider:
            await self.w3.provider.disconnect()
        logger.info("Web3 client disconnected")

    async def get_latest_block(self) -> int:
        """Get the latest block number with retry logic."""
        if not self.w3:
            raise RuntimeError("Web3 client not initialized. Use async context manager.")

        for attempt in range(self.settings.max_retry_attempts):
            try:
                block_number = await self.w3.eth.block_number
                logger.debug(f"Latest block number: {block_number}")
                return block_number
            except (Web3Exception, asyncio.TimeoutError, ConnectionError) as e:
                if attempt < self.settings.max_retry_attempts - 1:
                    wait_time = min(
                        self.settings.retry_multiplier ** attempt * self.settings.retry_min_wait,
                        self.settings.retry_max_wait
                    )
                    logger.warning(f"Error getting latest block (attempt {attempt + 1}): {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to get latest block after {self.settings.max_retry_attempts} attempts")
                    raise

    async def get_logs(
        self,
        from_block: int,
        to_block: int,
        topics: list[str]
    ) -> list[dict]:
        """
        Fetch logs with retry logic.

        Args:
            from_block: Starting block number
            to_block: Ending block number
            topics: List of topics to filter by

        Returns:
            List of log entries
        """
        if not self.w3:
            raise RuntimeError("Web3 client not initialized. Use async context manager.")

        filter_params = {
            'fromBlock': from_block,
            'toBlock': to_block,
            'topics': topics
        }

        logger.debug(f"Fetching logs from block {from_block} to {to_block}")

        for attempt in range(self.settings.max_retry_attempts):
            try:
                logs = await self.w3.eth.get_logs(filter_params)
                logger.debug(f"Retrieved {len(logs)} logs")
                return [dict(log) for log in logs]
            except (Web3Exception, asyncio.TimeoutError, ConnectionError) as e:
                if attempt < self.settings.max_retry_attempts - 1:
                    wait_time = min(
                        self.settings.retry_multiplier ** attempt * self.settings.retry_min_wait,
                        self.settings.retry_max_wait
                    )
                    logger.warning(f"Error fetching logs (attempt {attempt + 1}): {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch logs after {self.settings.max_retry_attempts} attempts")
                    raise

    async def get_approval_logs(
        self,
        owner_address: str,
        from_block: int,
        to_block: int
    ) -> list[dict]:
        """
        Fetch ERC-20 approval events where the given address is the owner.

        Args:
            owner_address: Ethereum address that granted approvals
            from_block: Starting block number
            to_block: Ending block number

        Returns:
            List of approval event logs
        """
        padded_owner = pad_address(owner_address)

        topics = [
            self.APPROVAL_EVENT_SIGNATURE,  # topic0: event signature
            padded_owner,                    # topic1: owner address
        ]

        return await self.get_logs(from_block, to_block, topics)

    async def get_all_approval_logs(self, owner_address: str, latest_block: int) -> list[dict]:
        """
        Fetch ALL approval events for an address using eth_getLogs.

        Strategy:
        1. Try querying full block range (0 to latest) first
        2. If that fails with "too many results", fall back to chunking

        Args:
            owner_address: Ethereum address to scan for approvals

        Returns:
            List of all approval log dictionaries
            :param latest_block:
        """
        if not self.w3:
            raise RuntimeError("Web3 client not initialized. Use async context manager.")

        logger.info(f"Fetching all approval events for {owner_address}")

        # Get latest block number
        logger.info(f"Latest block: {latest_block}")

        padded_owner = pad_address(owner_address)

        topics = [
            self.APPROVAL_EVENT_SIGNATURE,  # topic0: event signature
            padded_owner,                    # topic1: owner address
        ]

        try:
            # OPTION 1: Try full range first (0 to latest) - fastest if it works!
            logger.info(f"Attempting to fetch all approvals in single query (blocks 0 to {latest_block})...")
            logs = await self.get_logs(0, latest_block, topics)
            logger.info(f"✓ Successfully fetched {len(logs)} approval events in single query!")
            return logs

        except (Web3Exception, ValueError) as e:
            error_msg = str(e).lower()

            # Check if error is due to too many results
            if any(phrase in error_msg for phrase in [
                "query returned more than",
                "too many results",
                "result set too large",
                "exceeds maximum"
            ]):
                logger.warning(f"Query returned too many results. Falling back to chunking strategy...")
                return await self._fetch_with_chunking(owner_address, latest_block, topics)
            else:
                # Different error - re-raise
                logger.error(f"Unexpected error during full range query: {e}")
                raise

    async def _fetch_with_chunking(
        self,
        owner_address: str,
        latest_block: int,
        topics: list[str]
    ) -> list[dict]:
        """
        Fetch approval logs using chunking strategy.

        This is used as a fallback when the full range query returns too many results.
        Splits the blockchain into chunks and queries each chunk separately.

        Args:
            owner_address: Ethereum address to scan
            latest_block: Latest block number
            topics: Pre-formatted topic filters

        Returns:
            List of all approval log dictionaries
        """
        chunks = self._generate_chunks(0, latest_block, self.settings.blocks_per_chunk)
        total_chunks = len(chunks)

        logger.info(f"Scanning {latest_block + 1} blocks in {total_chunks} chunks of {self.settings.blocks_per_chunk} blocks")

        # Process chunks concurrently with semaphore to limit parallelism
        semaphore = asyncio.Semaphore(self.settings.max_concurrent_chunks)
        all_logs = []

        async def fetch_chunk_with_limit(chunk_num: int, start: int, end: int):
            """Fetch a single chunk with concurrency limiting."""
            async with semaphore:
                logger.info(f"Processing chunk {chunk_num}/{total_chunks} (blocks {start}-{end})")
                try:
                    logs = await self.get_logs(start, end, topics)
                    logger.info(f"Chunk {chunk_num}/{total_chunks} complete: found {len(logs)} events")
                    return logs
                except Exception as e:
                    logger.error(f"Chunk {chunk_num}/{total_chunks} failed: {e}")
                    raise

        # Create tasks for all chunks
        tasks = [
            fetch_chunk_with_limit(i + 1, start, end)
            for i, (start, end) in enumerate(chunks)
        ]

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Chunk {i + 1} failed: {result}")
                # Continue processing other chunks even if one fails
            else:
                all_logs.extend(result)

        logger.info(f"Chunked scan complete: fetched {len(all_logs)} total approval events")
        return all_logs

    @staticmethod
    def _generate_chunks(start: int, end: int, chunk_size: int) -> list[tuple[int, int]]:
        """
        Generate block range chunks.

        Args:
            start: Starting block number
            end: Ending block number
            chunk_size: Size of each chunk

        Returns:
            List of (start_block, end_block) tuples
        """
        chunks = []
        current = start

        while current <= end:
            chunk_end = min(current + chunk_size - 1, end)
            chunks.append((current, chunk_end))
            current = chunk_end + 1

        return chunks

    async def get_block(self, block_number: int) -> dict:
        """
        Get block details by number with retry logic.

        Args:
            block_number: Block number to fetch

        Returns:
            Block details dictionary
        """
        if not self.w3:
            raise RuntimeError("Web3 client not initialized. Use async context manager.")

        for attempt in range(self.settings.max_retry_attempts):
            try:
                block = await self.w3.eth.get_block(block_number)
                return dict(block)
            except (Web3Exception, asyncio.TimeoutError, ConnectionError) as e:
                if attempt < self.settings.max_retry_attempts - 1:
                    wait_time = min(
                        self.settings.retry_multiplier ** attempt * self.settings.retry_min_wait,
                        self.settings.retry_max_wait
                    )
                    logger.warning(f"Error getting block {block_number} (attempt {attempt + 1}): {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to get block {block_number} after {self.settings.max_retry_attempts} attempts")
                    raise

    async def get_token_symbol(self, token_address: str) -> str:
        """
        Get ERC-20 token symbol.

        Args:
            token_address: Token contract address

        Returns:
            Token symbol or "UnknownERC20" if unable to fetch
        """
        if not self.w3:
            raise RuntimeError("Web3 client not initialized. Use async context manager.")

        try:
            # ERC-20 symbol() function signature
            function_signature = "0x95d89b41"  # Keccak256("symbol()")[:4]

            call_data = {
                'to': token_address,
                'data': function_signature
            }

            result = await self.w3.eth.call(call_data)

            # Decode the result (ABI encoded string)
            if result and len(result) > 0:
                # Simple string decoding - skip offset/length and decode UTF-8
                try:
                    # Result format: offset(32) + length(32) + data
                    # Skip first 64 bytes (offset + length), decode rest
                    symbol_bytes = bytes(result[64:]).rstrip(b'\x00')
                    return symbol_bytes.decode('utf-8', errors='ignore').strip()
                except Exception:
                    pass

            return "UnknownERC20"

        except Exception as e:
            logger.debug(f"Failed to fetch symbol for token {token_address}: {e}")
            return "UnknownERC20"

    async def get_token_name(self, token_address: str) -> str:
        """
        Get ERC-20 token name.

        Args:
            token_address: Token contract address

        Returns:
            Token name or "UnknownERC20" if unable to fetch
        """
        if not self.w3:
            raise RuntimeError("Web3 client not initialized. Use async context manager.")

        try:
            # ERC-20 name() function signature
            function_signature = "0x06fdde03"  # Keccak256("name()")[:4]

            call_data = {
                'to': token_address,
                'data': function_signature
            }

            result = await self.w3.eth.call(call_data)

            # Decode the result (ABI encoded string)
            if result and len(result) > 0:
                # Simple string decoding - skip offset/length and decode UTF-8
                try:
                    # Result format: offset(32) + length(32) + data
                    # Skip first 64 bytes (offset + length), decode rest
                    name_bytes = bytes(result[64:]).rstrip(b'\x00')
                    return name_bytes.decode('utf-8', errors='ignore').strip()
                except Exception:
                    pass

            return "UnknownERC20"

        except Exception as e:
            logger.debug(f"Failed to fetch name for token {token_address}: {e}")
            return "UnknownERC20"

import logging
from datetime import datetime

from ..clients.web3_client import Web3Client
from approvalfetcher.model.approval import ApprovalEvent, ApprovalEventCollection
from ..utils.config import get_settings

logger = logging.getLogger(__name__)


class ApprovalService:
    """Service for fetching and processing ERC-20 approval events."""

    def __init__(self, client: Web3Client):
        """
        Initialize approval service.

        Args:
            client: Initialized Web3Client instance
        """
        self.client = client
        self.settings = get_settings()
        self._block_cache = {}

    async def fetch_all_approvals(self, owner_address: str) -> ApprovalEventCollection:
        """
        Fetch all approval events for a given owner address using eth_getLogs.

        This method uses the Web3Client's get_all_approval_logs() which:
        1. Tries to fetch all logs in a single query (fast!)
        2. Falls back to chunking if the query returns too many results

        Args:
            owner_address: Ethereum address to scan for approvals

        Returns:
            ApprovalEventCollection with all found events (latest only per token/spender pair)
        """
        logger.info(f"Starting approval event scan for address: {owner_address}")

        # Get latest block for metadata
        latest_block = await self.client.get_latest_block()

        # Fetch all approval logs using the new approach
        # (tries full range first, falls back to chunking if needed)
        logs = await self.client.get_all_approval_logs(owner_address, latest_block)
        logger.info(f"Retrieved {len(logs)} total approval events")

        # Parse logs into ApprovalEvent objects
        all_events = []
        for log in logs:
            try:
                event = await self._parse_log_to_event(log, owner_address)
                all_events.append(event)
            except Exception as e:
                logger.warning(f"Failed to parse log {log.get('transactionHash')}: {e}")

        logger.info(f"Successfully parsed {len(all_events)} approval events")

        # Filter to keep only the latest approval for each (token, spender) pair
        latest_approvals = self._filter_latest_approvals(all_events)
        logger.info(f"After filtering duplicates: {len(latest_approvals)} unique approvals remain")

        return ApprovalEventCollection(
            address=owner_address.lower(),
            total_events=len(latest_approvals),
            scanned_blocks=latest_block + 1,
            events=sorted(latest_approvals, key=lambda e: e.block_number),
            fetched_at=datetime.utcnow()
        )

    async def _parse_log_to_event(self, log: dict, owner_address: str) -> ApprovalEvent:
        """
        Parse a raw Web3 log entry into an ApprovalEvent.

        Args:
            log: Raw log dictionary from Web3
            owner_address: Owner address (for validation)

        Returns:
            ApprovalEvent object
        """
        topics = log['topics']

        # Extract spender from topic2 (last 40 chars, add 0x prefix)
        spender_topic = topics[2] if isinstance(topics[2], str) else topics[2].hex()
        spender = "0x" + spender_topic[-40:]

        # Extract value from data field
        data = log['data'] if isinstance(log['data'], str) else log['data'].hex()

        # Get block number
        block_number = log['blockNumber']
        if isinstance(block_number, str):
            block_number = int(block_number, 16)

        # Get timestamp from block (with caching)
        timestamp = await self._get_block_timestamp(block_number)

        # Get transaction hash
        tx_hash = log['transactionHash'] if isinstance(log['transactionHash'], str) else log['transactionHash'].hex()

        # Get token address
        token_address = log['address'] if isinstance(log['address'], str) else log['address'].hex()

        # Fetch token metadata (symbol and name)
        token_symbol = await self.client.get_token_symbol(token_address)
        token_name = await self.client.get_token_name(token_address)

        return ApprovalEvent(
            block_number=block_number,
            timestamp=timestamp,
            transaction_hash=tx_hash,
            token_address=token_address,
            token_name=token_name,
            token_symbol=token_symbol,
            owner=owner_address.lower(),
            spender=spender.lower(),
            value=data
        )

    async def _get_block_timestamp(self, block_number: int) -> datetime:
        """
        Get timestamp for a block (with caching).

        Args:
            block_number: Block number

        Returns:
            datetime object
        """
        if block_number in self._block_cache:
            return self._block_cache[block_number]

        try:
            block = await self.client.get_block(block_number)
            timestamp = datetime.fromtimestamp(block['timestamp'])
            self._block_cache[block_number] = timestamp
            return timestamp
        except Exception as e:
            logger.warning(f"Failed to fetch block {block_number} timestamp: {e}")
            # Return current time as fallback
            return datetime.utcnow()

    @staticmethod
    def _filter_latest_approvals(events: list[ApprovalEvent]) -> list[ApprovalEvent]:
        """
        Filter events to keep only the latest approval for each (token, spender) pair.

        When multiple approvals exist for the same token and spender, only the most recent
        one (highest block number) is relevant, as it overrides all previous approvals.
        This handles revocations (value=0) and approval updates.

        Args:
            events: List of all approval events

        Returns:
            List of approval events with only the latest for each (token, spender) pair
        """
        # Dictionary to store latest approval for each (token, spender) pair
        latest_by_pair = {}

        for event in events:
            # Create unique key for (token_address, spender) pair
            key = (event.token_address.lower(), event.spender.lower())

            # Keep the event with the highest block number for each pair
            if key not in latest_by_pair or event.block_number > latest_by_pair[key].block_number:
                latest_by_pair[key] = event

        return list(latest_by_pair.values())

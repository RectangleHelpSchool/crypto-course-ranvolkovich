import asyncio
import logging
from web3.types import LogReceipt

from ..clients.web3_client import Web3Client
from approvalfetcher.model.approval import ApprovalEvent, ApprovalEvents
from ..utils.config import get_settings
from ..utils.formatters import normalize_approval_amount
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ApprovalService:

    def __init__(self, client: Web3Client):
        self.client = client
        self.settings = get_settings()

    async def fetch_all_approvals(self, owner_address: str) -> ApprovalEvents:
        logger.info(f"Starting approval event scan for address: {owner_address}")

        logs = await self.client.get_all_approval_logs(owner_address)
        logger.info(f"Retrieved {len(logs)} total approval events")

        tasks = [self._parse_log_to_event(log, owner_address) for log in logs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        events_with_block: list[tuple[ApprovalEvent, int]] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                tx_hash = logs[i].get('transactionHash')
                tx_hash_str = tx_hash.hex() if isinstance(tx_hash, bytes) else str(tx_hash)
                logger.warning(f"Failed to parse log {tx_hash_str}: {result}")
            else:
                assert isinstance(result, ApprovalEvent)
                block_number = logs[i]['blockNumber']
                block_num_int = int(block_number) if isinstance(block_number, int) else block_number
                events_with_block.append((result, block_num_int))

        logger.info(f"Successfully parsed {len(events_with_block)} approval events")

        latest_approvals = self._filter_latest_approvals(events_with_block)
        logger.info(f"After filtering duplicates: {len(latest_approvals)} unique approvals remain")

        latest_block = await self.client.get_latest_block()

        return ApprovalEvents(
            address=owner_address.lower(),
            total_events=len(latest_approvals),
            scanned_blocks=latest_block + 1,
            events=latest_approvals,
            fetched_at=datetime.now(timezone.utc)
        )

    async def _parse_log_to_event(self, log: LogReceipt, owner_address: str) -> ApprovalEvent:
        topics = log['topics']

        spender_topic = topics[2].hex()
        spender = "0x" + spender_topic[-40:]

        data = log['data'].hex()
        token_address = log['address']

        token_symbol, token_name = await asyncio.gather(
            self.client.get_token_symbol(token_address),
            self.client.get_token_name(token_address)
        )

        value = normalize_approval_amount(data)

        return ApprovalEvent(
            token_address=token_address,
            token_name=token_name,
            token_symbol=token_symbol,
            owner=owner_address.lower(),
            spender=spender.lower(),
            value=value
        )

    @staticmethod
    def _filter_latest_approvals(events_with_block: list[tuple[ApprovalEvent, int]]) -> list[ApprovalEvent]:
        latest_by_token: dict[str, tuple[ApprovalEvent, int]] = {}

        for event, block_number in events_with_block:
            key = event.token_address.lower()
            if key not in latest_by_token or block_number > latest_by_token[key][1]:
                latest_by_token[key] = (event, block_number)

        return [event for event, _ in latest_by_token.values()]

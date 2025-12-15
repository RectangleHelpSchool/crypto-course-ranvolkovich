import asyncio
import logging
from datetime import datetime

from ..clients.web3_client import Web3Client
from approvalfetcher.model.approval import ApprovalEvent, ApprovalEventCollection
from ..utils.config import get_settings

logger = logging.getLogger(__name__)


class ApprovalService:

    def __init__(self, client: Web3Client):
        self.client = client
        self.settings = get_settings()

    async def fetch_all_approvals(self, owner_address: str) -> ApprovalEventCollection:
        logger.info(f"Starting approval event scan for address: {owner_address}")

        logs = await self.client.get_all_approval_logs(owner_address)
        logger.info(f"Retrieved {len(logs)} total approval events")

        tasks = [self._parse_log_to_event(log, owner_address) for log in logs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        events_with_block = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to parse log {logs[i].get('transactionHash')}: {result}")
            else:
                block_number = logs[i]['blockNumber']
                if isinstance(block_number, str):
                    block_number = int(block_number, 16)
                events_with_block.append((result, block_number))

        logger.info(f"Successfully parsed {len(events_with_block)} approval events")

        latest_approvals = self._filter_latest_approvals(events_with_block)
        logger.info(f"After filtering duplicates: {len(latest_approvals)} unique approvals remain")

        latest_block = await self.client.get_latest_block()

        return ApprovalEventCollection(
            address=owner_address.lower(),
            total_events=len(latest_approvals),
            scanned_blocks=latest_block + 1,
            events=latest_approvals,
            fetched_at=datetime.utcnow()
        )

    async def _parse_log_to_event(self, log: dict, owner_address: str) -> ApprovalEvent:
        topics = log['topics']

        spender_topic = topics[2] if isinstance(topics[2], str) else topics[2].hex()
        spender = "0x" + spender_topic[-40:]

        data = log['data'] if isinstance(log['data'], str) else log['data'].hex()

        token_address = log['address'] if isinstance(log['address'], str) else log['address'].hex()

        token_symbol, token_name = await asyncio.gather(
            self.client.get_token_symbol(token_address),
            self.client.get_token_name(token_address)
        )

        return ApprovalEvent(
            token_address=token_address,
            token_name=token_name,
            token_symbol=token_symbol,
            owner=owner_address.lower(),
            spender=spender.lower(),
            value=data
        )

    @staticmethod
    def _filter_latest_approvals(events_with_block: list[tuple[ApprovalEvent, int]]) -> list[ApprovalEvent]:
        latest_by_pair = {}

        for event, block_number in events_with_block:
            key = (event.token_address.lower(), event.spender.lower())
            if key not in latest_by_pair or block_number > latest_by_pair[key][1]:
                latest_by_pair[key] = (event, block_number)

        return [event for event, _ in latest_by_pair.values()]

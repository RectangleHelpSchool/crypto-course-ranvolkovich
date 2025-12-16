import logging
from .clients.web3_client import Web3Client
from .services.approval_service import ApprovalService
from approvalfetcher.model.approval import ApprovalEventCollection

logger = logging.getLogger(__name__)


class ApprovalFetcherApp:

    def __init__(self, client: Web3Client):
        self.client = client

    async def get_approvals(self, address: str) -> ApprovalEventCollection:
        logger.info(f"Starting approval event fetch for address: {address}")

        try:
            service = ApprovalService(self.client)
            approval_logs  = await service.fetch_all_approvals(address)
            logger.info(f"✓ Successfully fetched {approval_logs.total_events} approval events")
            return approval_logs

        except ConnectionError:
            logger.exception("Connection error")
            raise RuntimeError("Failed to connect to Infura")

        except Exception:
            logger.exception("Error fetching approval events")
            raise

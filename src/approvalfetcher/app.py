import logging
from typing import Optional
from .clients.web3_client import Web3Client
from .services.approval_service import ApprovalService
from approvalfetcher.model.approval import ApprovalEventCollection
from .utils.config import get_settings
from .utils.logging_config import setup_logging
from .utils.eth_utils import hex_to_int

logger = logging.getLogger(__name__)


class ApprovalFetcherApp:
    """Main application orchestrator for ERC-20 approval event fetching using Web3.py."""

    def __init__(
        self,
        infura_api_key: Optional[str] = None,
        log_level: Optional[str] = None
    ):
        """
        Initialize the application.

        Args:
            infura_api_key: Optional Infura API key (overrides .env)
            log_level: Optional log level (overrides .env)
        """
        self.settings = get_settings()
        self.infura_api_key = infura_api_key
        self.log_level = log_level or self.settings.log_level

        # Setup logging
        setup_logging(self.log_level)

    async def run(self, address: str) -> str:
        """
        Main application flow - fetch and format approval events using eth_getLogs.

        Strategy:
        1. Try querying full block range (0 to latest) first for speed
        2. Fall back to chunking if query returns too many results

        Args:
            address: Ethereum address to scan for approval events

        Returns:
            Formatted string with approval events
        """
        logger.info(f"Starting approval event fetch for address: {address}")

        # Get Infura API key
        infura_key = self.infura_api_key or self.settings.infura_api_key

        if not infura_key:
            raise ValueError(
                "No Infura API key configured!\n"
                "Please set INFURA_API_KEY in your .env file or pass --infura-key\n"
                "Get a free API key at: https://infura.io/"
            )

        try:
            async with Web3Client(infura_key) as client:
                service = ApprovalService(client)
                collection = await service.fetch_all_approvals(address)

                logger.info(f"✓ Successfully fetched {collection.total_events} approval events")
                return self._format_output(collection)

        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise RuntimeError(f"Failed to connect to Infura: {e}")

        except Exception as e:
            logger.error(f"Error fetching approval events: {e}", exc_info=True)
            raise

    @staticmethod
    def _format_output(collection: ApprovalEventCollection) -> str:
        """
        Format ApprovalEventCollection as human-readable text.

        Format: "approval on [TOKEN] to [SPENDER] on amount of [AMOUNT]"

        Args:
            collection: Collection of approval events

        Returns:
            Formatted string with one approval per line
        """
        if collection.total_events == 0:
            return "No approval events found."

        lines = []
        for event in collection.events:
            # Use symbol if available, otherwise use name, otherwise "UnknownERC20"
            token_display = event.token_symbol or event.token_name or "UnknownERC20"

            # Convert hex value to decimal integer
            amount = hex_to_int(event.value)

            # Shorten spender address for readability (first 6 + last 4 chars)
            spender_short = f"{event.spender[:6]}...{event.spender[-4:]}"

            # Format output line
            lines.append(f"approval on {token_display} to {spender_short} on amount of {amount}")

        return "\n".join(lines)

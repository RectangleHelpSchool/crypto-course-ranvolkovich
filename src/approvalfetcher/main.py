import asyncio
import sys

from approvalfetcher.services.approval_service import ApprovalService
from approvalfetcher.utils.cli import parse_args
from approvalfetcher.utils.logging_config import setup_logging
from approvalfetcher.utils.config import get_settings
from approvalfetcher.utils.formatters import format_approval_text
from approvalfetcher.clients.web3_client import Web3Client
from approvalfetcher.app import ApprovalFetcherApp
from approvalfetcher.model.approval import ApprovalEvents


async def run_approval_fetcher(address: str, approval_fetcher_app: ApprovalFetcherApp) -> ApprovalEvents:
    return await approval_fetcher_app.get_approvals(address)


async def run_cli(address: str) -> str:
    async with Web3Client() as client:
        approval_service = ApprovalService(client)
        approval_fetcher_app = ApprovalFetcherApp(approval_service)
        approval_events = await run_approval_fetcher(address, approval_fetcher_app)
        return format_approval_text(approval_events)

def main() -> None:
    args = parse_args()
    settings = get_settings()
    setup_logging(settings.log_level)

    try:
        result = asyncio.run(run_cli(args.address))
        print(result)
        sys.exit(0)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
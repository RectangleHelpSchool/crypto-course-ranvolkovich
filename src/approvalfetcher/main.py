import asyncio
import sys
from pydantic import ValidationError
from approvalfetcher.utils.cli import parse_args
from approvalfetcher.utils.logging_config import setup_logging
from approvalfetcher.utils.config import get_settings
from approvalfetcher.utils.formatters import format_approval_text
from approvalfetcher.clients.web3_client import Web3Client
from approvalfetcher.app import ApprovalFetcherApp
from approvalfetcher.model.approval import ApprovalEventCollection


async def run_approval_fetcher(address: str, client: Web3Client) -> ApprovalEventCollection:
    app = ApprovalFetcherApp(client)
    return await app.get_approvals(address)


async def run_cli(address: str) -> str:
    async with Web3Client() as client:
        collection = await run_approval_fetcher(address, client)
        return format_approval_text(collection)

def main() -> None:
    args = parse_args()

    try:
        settings = get_settings()
    except ValidationError as e:
        for error in e.errors():
            if error['loc'][0] == 'infura_api_key':
                print(f"Error: {error['msg']}", file=sys.stderr)
                sys.exit(1)
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

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
import argparse
from typing import Optional

from approvalfetcher.utils.valdation.eth_validtor import eth_address


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments for the approval fetcher."""
    parser = argparse.ArgumentParser(
        prog="approval-fetcher",
        description="Fetch ERC-20 token approval events for an Ethereum address using eth_getLogs",
        epilog="Example: approval-fetcher --address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --infura-key YOUR_KEY",
    )

    parser.add_argument(
        "--address",
        type=eth_address,
        required=True,
        help="Ethereum address to scan for approval events (owner)"
    )

    parser.add_argument(
        "--infura-key",
        type=str,
        help="Infura API key (overrides .env) - Get free key at https://infura.io/"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )

    return parser.parse_args(args)
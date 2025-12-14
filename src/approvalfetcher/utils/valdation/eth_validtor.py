import argparse
import re

ETH_ADDRESS_REGEX = re.compile(r"^0x[a-fA-F0-9]{40}$")

def eth_address(value: str) -> str:
    if not ETH_ADDRESS_REGEX.match(value):
        raise argparse.ArgumentTypeError(
            f"Invalid Ethereum address: {value}"
        )
    return value
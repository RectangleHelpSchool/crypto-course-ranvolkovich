import argparse
from web3 import Web3


def eth_address(value: str) -> str:
    if not Web3.is_address(value):
        raise argparse.ArgumentTypeError(
            f"Invalid Ethereum address: {value}"
        )
    return value
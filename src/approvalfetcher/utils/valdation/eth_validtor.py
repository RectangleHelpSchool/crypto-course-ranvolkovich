from web3 import Web3


def eth_address(value: str) -> str:
    lower_value = value.lower()
    if not Web3.is_address(lower_value):
        raise ValueError(f"Invalid Ethereum address: {lower_value}")
    return value
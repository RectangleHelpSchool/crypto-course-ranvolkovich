
def pad_address(address: str) -> str:
    """
    Convert Ethereum address to padded 32-byte hex for topic filtering.

    Args:
        address: Ethereum address (e.g., 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0)

    Returns:
        Padded address (e.g., 0x000000000000000000000000742d35cc6634c0532925a3b844bc9e7595f0beb0)

    Example:
        >>> pad_address("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0")
        '0x000000000000000000000000742d35cc6634c0532925a3b844bc9e7595f0beb0'
    """
    # Remove 0x prefix, convert to lowercase, pad to 64 chars, add 0x prefix
    clean_address = address[2:] if address.startswith('0x') else address
    return "0x" + clean_address.lower().zfill(64)


def hex_to_int(hex_value: str) -> int:
    """
    Convert hex string to integer.

    Args:
        hex_value: Hex string (with or without 0x prefix)

    Returns:
        Integer value

    Example:
        >>> hex_to_int("0xff")
        255
        >>> hex_to_int("ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff")
        115792089237316195423570985008687907853269984665640564039457584007913129639935
    """
    # Remove 0x prefix if present
    clean_hex = hex_value[2:] if hex_value.startswith('0x') else hex_value
    return int(clean_hex, 16)

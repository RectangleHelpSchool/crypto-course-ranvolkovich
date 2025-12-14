import pytest
from approvalfetcher.utils.cli import parse_args


def test_parse_args_with_valid_address():
    """Test argument parsing with valid Ethereum address."""
    args = parse_args(["--address", "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"])
    assert args.address == "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
    assert args.log_level == "INFO"  # Default


def test_parse_args_with_infura_key():
    """Test argument parsing with custom Infura key."""
    args = parse_args([
        "--address", "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
        "--infura-key", "test-key-123"
    ])
    assert args.infura_key == "test-key-123"


def test_parse_args_with_log_level():
    """Test argument parsing with custom log level."""
    args = parse_args([
        "--address", "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
        "--log-level", "DEBUG"
    ])
    assert args.log_level == "DEBUG"


def test_parse_args_invalid_address():
    """Test that invalid address raises error."""
    with pytest.raises(SystemExit):
        parse_args(["--address", "not-an-address"])
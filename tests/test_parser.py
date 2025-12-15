import pytest

from approvalfetcher.utils.cli import parse_args


def test_parse_args_invalid_address():
    with pytest.raises(SystemExit):
        parse_args(["--address", "not-an-address"])

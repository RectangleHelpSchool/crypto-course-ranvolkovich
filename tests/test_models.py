from datetime import datetime
from approvalfetcher.model.approval import ApprovalEvent, ApprovalEventCollection


def test_approval_event_creation():
    """Test ApprovalEvent model creation."""
    event = ApprovalEvent(
        block_number=19123456,
        timestamp=datetime(2025, 12, 14, 10, 30, 0),
        transaction_hash="0xabc123",
        token_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
        owner="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        spender="0x1111111254fb6c44bac0bed2854e76f90643097d",
        value="0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    )

    assert event.block_number == 19123456
    assert event.owner == "0x742d35cc6634c0532925a3b844bc9e7595f0beb"  # Lowercase
    assert event.spender == "0x1111111254fb6c44bac0bed2854e76f90643097d"


def test_approval_event_timestamp_parsing():
    """Test timestamp parsing from string."""
    event = ApprovalEvent(
        block_number=19123456,
        timestamp="1702554600",  # String timestamp
        transaction_hash="0xabc123",
        token_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
        owner="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        spender="0x1111111254fb6c44bac0bed2854e76f90643097d",
        value="0x0"
    )

    assert isinstance(event.timestamp, datetime)


def test_approval_event_collection():
    """Test ApprovalEventCollection model."""
    event1 = ApprovalEvent(
        block_number=100,
        timestamp=datetime.utcnow(),
        transaction_hash="0xabc",
        token_address="0xdef",
        owner="0x123",
        spender="0x456",
        value="0x0"
    )

    event2 = ApprovalEvent(
        block_number=200,
        timestamp=datetime.utcnow(),
        transaction_hash="0xghi",
        token_address="0xjkl",
        owner="0x123",
        spender="0x789",
        value="0x1"
    )

    collection = ApprovalEventCollection(
        address="0x123",
        total_events=2,
        scanned_blocks=1000,
        events=[event1, event2]
    )

    assert collection.address == "0x123"
    assert collection.total_events == 2
    assert collection.scanned_blocks == 1000
    assert len(collection.events) == 2

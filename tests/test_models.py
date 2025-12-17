from approvalfetcher.model.approval import ApprovalEvent, ApprovalEvents


def test_approval_event_creation():
    event = ApprovalEvent(
        token_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
        owner="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        spender="0x1111111254fb6c44bac0bed2854e76f90643097d",
        value="0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    )

    assert event.owner == "0x742d35cc6634c0532925a3b844bc9e7595f0beb"
    assert event.spender == "0x1111111254fb6c44bac0bed2854e76f90643097d"
    assert event.token_address == "0xdac17f958d2ee523a2206206994597c13d831ec7"


def test_approval_event_with_token_metadata():
    event = ApprovalEvent(
        token_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
        token_name="Tether USD",
        token_symbol="USDT",
        owner="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        spender="0x1111111254fb6c44bac0bed2854e76f90643097d",
        value="0x0"
    )

    assert event.token_name == "Tether USD"
    assert event.token_symbol == "USDT"


def test_approval_event_collection():
    event1 = ApprovalEvent(
        token_address="0xdef",
        owner="0x123",
        spender="0x456",
        value="0x0"
    )

    event2 = ApprovalEvent(
        token_address="0xjkl",
        owner="0x123",
        spender="0x789",
        value="0x1"
    )

    collection = ApprovalEvents(
        address="0x123",
        total_events=2,
        scanned_blocks=1000,
        events=[event1, event2]
    )

    assert collection.address == "0x123"
    assert collection.total_events == 2
    assert collection.scanned_blocks == 1000
    assert len(collection.events) == 2

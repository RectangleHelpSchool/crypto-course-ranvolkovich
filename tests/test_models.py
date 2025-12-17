from approvalfetcher.model.approval import ApprovalEvent, ApprovalEvents


def test_approval_event_creation():
    event = ApprovalEvent(
        token_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
        spender="0x1111111254fb6c44bac0bed2854e76f90643097d",
        value="0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    )

    assert event.spender == "0x1111111254fb6c44bac0bed2854e76f90643097d"
    assert event.token_address == "0xdAC17F958D2ee523a2206206994597C13D831ec7"


def test_approval_event_with_token_metadata():
    event = ApprovalEvent(
        token_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
        token_symbol="USDT",
        spender="0x1111111254fb6c44bac0bed2854e76f90643097d",
        value="0x0"
    )

    assert event.token_symbol == "USDT"


def test_approval_event_collection():
    event1 = ApprovalEvent(
        token_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
        spender="0x1111111254fb6c44bac0bed2854e76f90643097d",
        value="0x0"
    )

    event2 = ApprovalEvent(
        token_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        spender="0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
        value="0x1"
    )

    collection = ApprovalEvents(
        address="0x1111111254fb6c44bac0bed2854e76f90643097d",
        total_events=2,
        scanned_blocks=1000,
        events=[event1, event2]
    )

    assert collection.address == "0x1111111254fb6c44bac0bed2854e76f90643097d"
    assert collection.total_events == 2
    assert collection.scanned_blocks == 1000
    assert len(collection.events) == 2

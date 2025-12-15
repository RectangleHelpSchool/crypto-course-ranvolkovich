from approvalfetcher.model.approval import ApprovalEventCollection
from .eth_utils import hex_to_int


def format_approval_text(collection: ApprovalEventCollection) -> str:
    if collection.total_events == 0:
        return "No approval events found."
    lines = []
    for event in collection.events:
        token_display = event.token_symbol or event.token_name or "UnknownERC20"
        amount = hex_to_int(event.value)
        spender_short = f"{event.spender[:6]}...{event.spender[-4:]}"
        lines.append(f"approval on {token_display} to {spender_short} on amount of {amount}")
    return "\n".join(lines)

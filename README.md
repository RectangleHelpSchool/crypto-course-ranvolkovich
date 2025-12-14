# ERC-20 Approval Event Fetcher

A production-grade Python CLI tool for fetching ERC-20 token approval events from Ethereum blockchain using async Web3.py with Infura RPC and `eth_getLogs`.

## Features

- **Fast eth_getLogs Strategy**: Tries full block range first, falls back to chunking only if needed
- **Token Metadata Fetching**: Automatically retrieves token names and symbols
- **Async Architecture**: Uses `asyncio` and `aiohttp` for high-performance concurrent requests
- **Exponential Backoff Retry**: Automatic retry with exponential backoff for all RPC calls
- **Smart Chunking Fallback**: Only chunks when full range query returns too many results
- **Type Safety**: Full type hints with Pydantic models for data validation
- **Configurable**: Environment-based configuration with sensible defaults
- **Production-Ready**: Comprehensive error handling, logging, and resource cleanup

## Architecture

```
CLI Layer (utils/cli.py)
    ↓
Application Layer (app.py)
    ↓
Service Layer (approval_service.py)
    ↓
Client Layer (web3_client.py)
    ↓
Models Layer (model/approval.py)
```

## Installation

### Prerequisites

- Python 3.11 or higher
- Infura API key (free tier: https://infura.io/)

### Setup

1. Clone the repository:
```bash
cd crypto-course-ranvolkovich
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install the package:
```bash
pip install -e .
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your Infura API key
```

## Configuration

Edit `.env` file with your settings:

```env
INFURA_API_KEY=your_infura_key_here
INFURA_ENDPOINT=https://mainnet.infura.io/v3/
BLOCKS_PER_CHUNK=10000
MAX_CONCURRENT_CHUNKS=5
MAX_RETRY_ATTEMPTS=5
RETRY_MIN_WAIT=1
RETRY_MAX_WAIT=60
RETRY_MULTIPLIER=2
LOG_LEVEL=INFO
```

## Usage

### Basic Usage

```bash
approval-fetcher --address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```

### With Custom Infura Key

```bash
approval-fetcher --address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --infura-key YOUR_KEY
```

### With Debug Logging

```bash
approval-fetcher --address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --log-level DEBUG
```

### Save Output to File

```bash
approval-fetcher --address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb > approvals.txt
```

### Suppress Logs (Show Only Results)

```bash
approval-fetcher --address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --log-level WARNING
```

## CLI Options

```
usage: approval-fetcher [-h] --address ADDRESS [--infura-key INFURA_KEY] [--log-level {DEBUG,INFO,WARNING,ERROR}]

Fetch ERC-20 token approval events for an Ethereum address using eth_getLogs

options:
  -h, --help            show this help message and exit
  --address ADDRESS     Ethereum address to scan for approval events (owner)
  --infura-key INFURA_KEY
                        Infura API key (overrides .env) - Get free key at https://infura.io/
  --log-level {DEBUG,INFO,WARNING,ERROR}
                        Logging level (default: INFO)
```

## Output Format

The tool outputs human-readable text with one approval per line:

```
approval on SKL to 0x68b3...fc45 on amount of 115792089237316195423570985008687907853269984665640563830357584007913129639935
approval on USDT to 0x68b3...fc45 on amount of 115792089237316195423570985008687907853269984665640564039457584007913129639935
approval on USDT to 0x0000...8ba3 on amount of 115792089237316195423570985008687907853269984665640564039457584007913129639935
```

**Format**: `approval on [TOKEN_SYMBOL] to [SPENDER_ADDRESS] on amount of [AMOUNT]`

- **TOKEN_SYMBOL**: Token symbol (e.g., USDT, SKL) or "UnknownERC20" if unavailable
- **SPENDER_ADDRESS**: Shortened address of the approved spender (first 6 + last 4 chars)
- **AMOUNT**: Approval amount in wei (raw integer value)

**Note**: Large numbers like `115792089237316195...` represent "unlimited approvals" (uint256.max), a common pattern in DeFi where users approve the maximum possible value to avoid repeated approvals.

## How It Works

### ERC-20 Approval Event

The tool scans for the ERC-20 `Approval` event:

```solidity
event Approval(address indexed owner, address indexed spender, uint256 value)
```

**Event Signature**: `0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925`

### Important: Latest Approvals Only

**The tool returns only the LATEST approval for each unique (token, spender) pair.**

When an address approves the same spender multiple times for the same token, only the most recent approval is relevant, as it overrides all previous ones. This is critical because:

- ✅ **Approval Updates**: If you approve 100 tokens, then later approve 1000 tokens, only the 1000 approval matters
- ✅ **Revocations**: Setting approval to 0 revokes the approval (overrides previous non-zero approvals)
- ✅ **Active State**: You only see the current approval state, not the history

**Example:**
```
Block 1000: Approve USDT to Spender A for 100 tokens
Block 2000: Approve USDT to Spender A for 0 tokens (revocation)
Block 3000: Approve USDT to Spender A for 1000 tokens

Result: Only the Block 3000 approval is returned (1000 tokens)
```

### Test Examples

You can test with this example address: [`0x005e20fcf757b55d6e27dea9ba4f90c0b03ef852`](https://etherscan.io/address/0x005e20fcf757b55d6e27dea9ba4f90c0b03ef852)

Example transactions:
- **SKALE token approval** (infinite amount): [0x07a8b97798f16b854b7b5538550f0ddde27a0910c710714e16c1f51135e6bae8](https://etherscan.io/tx/0x07a8b97798f16b854b7b5538550f0ddde27a0910c710714e16c1f51135e6bae8)
- **USDT token approval**: [0xf3d8d7f12dc73863cd9714340f196156bc92125e61465cdfd4470f241c47a69b](https://etherscan.io/tx/0xf3d8d7f12dc73863cd9714340f196156bc92125e61465cdfd4470f241c47a69b)

### Scanning Strategy

1. **Get Latest Block**: Queries the current blockchain height
2. **Try Full Range First**: Attempts `eth_getLogs` on entire range (blocks 0 to latest) with topic filters
3. **Smart Fallback**: If "too many results" error, automatically falls back to chunking:
   - Divides blockchain into 10,000-block ranges
   - Processes up to 5 chunks concurrently
4. **Filter by Owner**: Uses topic filtering to get only approvals from the specified address
5. **Parse Events**: Extracts owner, spender, token address, and approval amount
6. **Fetch Token Metadata**: Retrieves token name and symbol via ERC-20 `name()` and `symbol()` calls
7. **Enrich with Timestamps**: Fetches block timestamps (with caching)
8. **Deduplicate**: Keeps only the latest approval for each (token, spender) pair
9. **Format Output**: Returns human-readable text with token symbols and shortened addresses

### Performance

- **Fast Path** (full range query): Usually **3-5 seconds** for most addresses
- **Fallback Path** (chunking): 10-20 minutes for addresses with many approvals
- **Ethereum Mainnet**: ~24M blocks as of December 2024
- **Optimization**: The tool automatically uses the fastest method available

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=approvalfetcher --cov-report=term-missing
```

### Project Structure

```
src/approvalfetcher/
├── __init__.py
├── main.py                        # Entry point
├── app.py                         # Application orchestration
├── clients/
│   ├── __init__.py
│   └── web3_client.py             # Async Web3 client with retry & token metadata
├── services/
│   ├── __init__.py
│   └── approval_service.py        # Business logic & event parsing
├── model/
│   ├── __init__.py
│   └── approval.py                # Pydantic data models
└── utils/
    ├── __init__.py
    ├── cli.py                     # CLI argument parsing
    ├── config.py                  # Configuration management
    ├── logging_config.py          # Logging setup
    ├── eth_utils.py               # Ethereum utilities (address padding, hex conversion)
    └── valdation/
        ├── __init__.py
        └── eth_validtor.py        # Address validation
```

## Technical Details

### Async Patterns

- **Context Managers**: Proper resource cleanup with `async with`
- **Concurrent Processing**: `asyncio.gather()` for parallel execution (in chunking fallback)
- **Semaphore Rate Limiting**: Controls concurrent RPC calls during chunking
- **Exponential Backoff**: Manual implementation with configurable parameters

### eth_getLogs with Topic Filtering

The tool uses Ethereum's `eth_getLogs` RPC method with topic filters for efficient querying:

```python
topics = [
    "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925",  # Approval event signature
    "0x000000000000000000000000[owner_address]"                                 # Padded owner address
]
```

This filters directly at the RPC level, retrieving only relevant approval events.

### Token Metadata Fetching

For each approval, the tool fetches ERC-20 token metadata using direct `eth_call`:

- **name()**: Function signature `0x06fdde03`
- **symbol()**: Function signature `0x95d89b41`
- **Fallback**: Returns "UnknownERC20" if calls fail

### Retry Strategy

- **Max Attempts**: 5 (configurable)
- **Wait Times**: 1s, 2s, 4s, 8s, 16s (exponential with max 60s)
- **Retry On**: Network errors, timeouts, RPC errors
- **Don't Retry On**: Invalid parameters, authentication errors

### Error Handling

- **Connection Errors**: Retry with exponential backoff
- **Rate Limits**: Automatic backoff and retry
- **Invalid Input**: Fail fast with clear error messages
- **Parsing Errors**: Log and skip individual events, continue processing

## Troubleshooting

### "Failed to connect to Infura endpoint"

- Check your Infura API key in `.env`
- Verify your internet connection
- Ensure the endpoint URL is correct

### "Rate limit exceeded"

- The free Infura tier has limits (100K requests/day)
- Reduce `MAX_CONCURRENT_CHUNKS` in `.env`
- Consider upgrading your Infura plan

### Slow Performance

- This is expected for addresses with many approvals
- The tool scans the entire blockchain history
- Consider optimizing by scanning only recent blocks if you don't need full history

## License

This project is part of a crypto course assignment.

## Contributing

This is a course project, but suggestions and improvements are welcome!

## Acknowledgments

- Built with [Web3.py](https://github.com/ethereum/web3.py)
- Uses [Infura](https://infura.io/) for Ethereum RPC access
- Data validation with [Pydantic](https://docs.pydantic.dev/)
- Async HTTP with [aiohttp](https://docs.aiohttp.org/)

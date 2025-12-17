# ERC-20 Approval Event Fetcher

A production-grade Python CLI tool for fetching ERC-20 token approval events from Ethereum blockchain using async Web3.py with Infura RPC and `eth_getLogs`.

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
LOG_LEVEL=INFO
```

## Usage

### Basic Usage

```bash
approval-fetcher --address 0x005e20fCf757B55D6E27dEA9BA4f90C0B03ef852
```

## CLI Options

```
usage: approval-fetcher [-h] --address ADDRESS

Fetch ERC-20 token approval events for an Ethereum address using eth_getLogs

options:
  -h, --help            show this help message and exit
  --address ADDRESS     Ethereum address to scan for approval events (owner)
```

All configuration (Infura API key, log level, etc.) is managed through the `.env` file.

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
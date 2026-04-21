# Binance Futures Testnet Trading Bot

A CLI + Web trading bot that places **Market** and **Limit** orders on the Binance Futures Testnet (USDT-M) with structured logging and error handling.

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST client (HMAC-SHA256 signing)
│   ├── orders.py          # Order placement logic
│   ├── validators.py      # Input validation
│   └── logging_config.py  # Dual-handler logging (console + file)
├── templates/
│   └── index.html         # Web dashboard UI
├── cli.py                 # CLI entry point (argparse)
├── app.py                 # Flask web dashboard
├── logs/
│   └── trading_bot.log    # Auto-created at runtime
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

### 1. Prerequisites

- Python 3.10+
- A [Binance Futures Testnet](https://testnet.binancefuture.com/) account with API credentials

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API credentials

```bash
cp .env.example .env
```

Edit `.env` and add your testnet API key and secret:

```
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

## Usage

### Option 1: CLI (Command Line)

**Place a Market order:**
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

**Place a Limit order:**
```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 50000
```

**Demo mode (no API keys needed):**
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --demo
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.05 --price 1800 --demo
```

### Option 2: Web Dashboard (Bonus Feature)

```bash
python app.py
```

Then open **http://localhost:5000** in your browser. The dashboard features:
- Live price ticker for BTC, ETH, BNB
- Visual order form with BUY/SELL and MARKET/LIMIT toggles
- Order history table with real-time updates
- Toast notifications for order status

### View CLI help

```bash
python cli.py --help
```

## CLI Arguments

| Argument     | Required   | Description                           |
|-------------|------------|---------------------------------------|
| `--symbol`  | Yes        | Trading pair (e.g. `BTCUSDT`)         |
| `--side`    | Yes        | `BUY` or `SELL`                       |
| `--type`    | Yes        | `MARKET` or `LIMIT`                   |
| `--quantity`| Yes        | Order quantity (e.g. `0.001`)          |
| `--price`   | LIMIT only | Limit price (e.g. `50000`)            |
| `--demo`    | No         | Run in demo mode (simulated orders)   |

## Output

The bot prints:
1. **Order Request Summary** - shows what will be sent
2. **Order Response** - `orderId`, `status`, `executedQty`, `avgPrice`, etc.
3. **Success/Failure message**

All API requests, responses, and errors are logged to `logs/trading_bot.log`.

## Error Handling

The bot handles:
- **Invalid input** - clear validation error messages
- **API errors** - Binance error codes and messages displayed
- **Network failures** - connection and timeout errors caught gracefully

## Assumptions

- Uses **direct REST calls** with HMAC-SHA256 signing
- Testnet base URL: `https://testnet.binancefuture.com`
- LIMIT orders default to `GTC` (Good-Til-Cancelled) time-in-force
- API credentials are loaded from a `.env` file in the project root
- Demo mode uses the Binance public API for real-time prices

"""
CLI entry point for the Trading Bot.

Usage:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
    python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.05 --price 3000
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --demo
"""

import argparse
import os
import sys

from dotenv import load_dotenv

from bot.logging_config import setup_logging
from bot.client import BinanceClient, BinanceAPIError
from bot.orders import place_market_order, place_limit_order


def print_separator():
    """Print a line to separate sections."""
    print("=" * 50)


def show_order_summary(args):
    """Show what order we're about to place."""
    print()
    print_separator()
    print("  ORDER REQUEST SUMMARY")
    print_separator()
    print(f"  Symbol   : {args.symbol.upper()}")
    print(f"  Side     : {args.side.upper()}")
    print(f"  Type     : {args.type.upper()}")
    print(f"  Quantity : {args.quantity}")
    if args.price is not None:
        print(f"  Price    : {args.price}")
    if args.demo:
        print(f"  Mode     : DEMO (simulated)")
    print_separator()


def show_order_result(result):
    """Show the order response from Binance."""
    print()
    print_separator()
    print("  ORDER RESPONSE")
    print_separator()
    for key, value in result.items():
        print(f"  {key:14s}: {value}")
    print_separator()


def create_parser():
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Place orders on Binance Futures Testnet (USDT-M).",
        epilog=(
            "Examples:\n"
            "  python cli.py --symbol BTCUSDT --side BUY  --type MARKET --quantity 0.001\n"
            "  python cli.py --symbol ETHUSDT --side SELL --type LIMIT  --quantity 0.05 --price 3000\n"
            "  python cli.py --symbol BTCUSDT --side BUY  --type MARKET --quantity 0.001 --demo\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--symbol", required=True, help="Trading pair (e.g. BTCUSDT)")
    parser.add_argument("--side", required=True, choices=["BUY", "SELL"], type=str.upper,
                        help="BUY or SELL")
    parser.add_argument("--type", required=True, choices=["MARKET", "LIMIT"], type=str.upper,
                        help="MARKET or LIMIT")
    parser.add_argument("--quantity", required=True, type=float, help="Order quantity (e.g. 0.001)")
    parser.add_argument("--price", type=float, default=None,
                        help="Limit price (required for LIMIT orders)")
    parser.add_argument("--demo", action="store_true",
                        help="Run in demo mode (simulates orders without needing API keys)")

    return parser


def main():
    """Main function - runs the trading bot CLI."""

    # Load environment variables from .env file
    load_dotenv()

    # Set up logging
    logger = setup_logging()

    # Parse command-line arguments
    parser = create_parser()
    args = parser.parse_args()

    # Check: LIMIT orders need a price
    if args.type == "LIMIT" and args.price is None:
        parser.error("--price is required when --type is LIMIT")

    # Get API credentials from .env file
    api_key = os.getenv("BINANCE_API_KEY", "")
    api_secret = os.getenv("BINANCE_API_SECRET", "")

    # If not in demo mode, we need real API keys
    if not args.demo and (not api_key or not api_secret):
        print("\nError: API credentials not found!")
        print("Create a .env file with your Binance testnet API key and secret.")
        print("Or use --demo flag to run in demo mode.")
        print("See .env.example for the template.\n")
        sys.exit(1)

    # Create the Binance client
    client = BinanceClient(api_key=api_key, api_secret=api_secret, demo=args.demo)

    # Show what we're about to do
    show_order_summary(args)

    # Place the order
    try:
        if args.type == "MARKET":
            result = place_market_order(client, args.symbol, args.side, args.quantity)
        else:
            result = place_limit_order(client, args.symbol, args.side, args.quantity, args.price)

        # Show the result
        show_order_result(result)
        print("\n  [SUCCESS] ORDER PLACED SUCCESSFULLY!\n")
        logger.info("Order completed! Order ID: %s", result.get("orderId"))

    except ValueError as e:
        logger.error("Validation error: %s", e)
        print(f"\n  [ERROR] Input Error: {e}\n")
        sys.exit(1)

    except BinanceAPIError as e:
        logger.error("API error: %s", e)
        print(f"\n  [ERROR] Binance Error: {e}\n")
        sys.exit(1)

    except ConnectionError as e:
        logger.error("Connection error: %s", e)
        print(f"\n  [ERROR] Network Error: {e}\n")
        sys.exit(1)

    except Exception as e:
        logger.error("Unexpected error: %s", e)
        print(f"\n  [ERROR] Something went wrong: {e}\n")
        sys.exit(1)


# Run the bot when this file is executed
if __name__ == "__main__":
    main()

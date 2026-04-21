"""
Flask web dashboard for the Trading Bot.
Provides a visual interface to place orders on Binance Futures Testnet.

Run with: python app.py
Then open http://localhost:5000 in your browser.
"""

import os
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from bot.logging_config import setup_logging
from bot.client import BinanceClient, BinanceAPIError
from bot.orders import place_market_order, place_limit_order

# Load env and set up logging
load_dotenv()
logger = setup_logging()

app = Flask(__name__)

# Store order history in memory
order_history = []


def get_client():
    """Create a Binance client. Uses real API if keys are set, demo mode otherwise."""
    api_key = os.getenv("BINANCE_API_KEY", "")
    api_secret = os.getenv("BINANCE_API_SECRET", "")
    # Auto-detect: use real API if keys exist, demo mode if not
    demo = not (api_key and api_secret)
    if demo:
        logger.info("No API keys found — running in DEMO mode (simulated orders)")
    else:
        logger.info("API keys found — running in LIVE TESTNET mode")
    return BinanceClient(api_key=api_key, api_secret=api_secret, demo=demo)


@app.route("/")
def index():
    """Render the main trading dashboard."""
    return render_template("index.html")


@app.route("/api/place-order", methods=["POST"])
def place_order():
    """API endpoint to place an order."""
    try:
        data = request.json
        symbol = data.get("symbol", "").upper()
        side = data.get("side", "").upper()
        order_type = data.get("type", "").upper()
        quantity = float(data.get("quantity", 0))
        price = data.get("price")

        if price:
            price = float(price)

        client = get_client()

        if order_type == "MARKET":
            result = place_market_order(client, symbol, side, quantity)
        elif order_type == "LIMIT":
            result = place_limit_order(client, symbol, side, quantity, price)
        else:
            return jsonify({"success": False, "error": "Invalid order type"})

        # Add to history
        order_history.insert(0, result)
        if len(order_history) > 20:
            order_history.pop()

        return jsonify({"success": True, "data": result})

    except ValueError as e:
        return jsonify({"success": False, "error": f"Validation Error: {e}"})
    except BinanceAPIError as e:
        return jsonify({"success": False, "error": f"API Error: {e}"})
    except ConnectionError as e:
        return jsonify({"success": False, "error": f"Network Error: {e}"})
    except Exception as e:
        return jsonify({"success": False, "error": f"Error: {e}"})


@app.route("/api/history")
def get_history():
    """Return order history."""
    return jsonify({"orders": order_history})


@app.route("/api/price/<symbol>")
def get_price(symbol):
    """Get current price for a symbol."""
    try:
        import requests as req
        r = req.get(
            "https://testnet.binancefuture.com/fapi/v1/ticker/price",
            params={"symbol": symbol.upper()},
            timeout=5
        )
        if r.status_code == 200:
            return jsonify({"success": True, "price": r.json()["price"]})
        return jsonify({"success": False, "error": "Could not fetch price"})
    except Exception:
        return jsonify({"success": False, "error": "Price unavailable"})


if __name__ == "__main__":
    print("\n  Trading Bot Dashboard running at: http://localhost:5000\n")
    app.run(debug=True, port=5000)

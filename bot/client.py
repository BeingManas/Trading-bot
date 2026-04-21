"""
Binance Futures Testnet API client.
Uses direct REST calls to connect and place orders.
Also supports a demo mode for testing without valid API keys.
"""

import hashlib
import hmac
import time
import random
import logging
from urllib.parse import urlencode

import requests

# Logger for this file
logger = logging.getLogger("trading_bot.client")

# Binance Futures Testnet base URL
BASE_URL = "https://testnet.binancefuture.com"


class BinanceAPIError(Exception):
    """Custom error for Binance API problems."""

    def __init__(self, status_code, error_code, message):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        super().__init__(f"Binance API Error (HTTP {status_code}): {message} (code: {error_code})")


class BinanceClient:
    """Simple client to interact with Binance Futures Testnet API."""

    def __init__(self, api_key, api_secret, demo=False):
        """
        Set up the client with API credentials.

        api_key: Your Binance testnet API key
        api_secret: Your Binance testnet API secret
        demo: If True, simulate orders without calling the real API
        """
        self.demo = demo

        if not demo:
            if not api_key or not api_secret:
                raise ValueError("API key and secret cannot be empty!")

        self.api_key = api_key or ""
        self.api_secret = api_secret or ""
        self.base_url = BASE_URL

        # Set up a session with the API key in headers
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
        })

        if demo:
            logger.info("Binance client ready in DEMO mode (simulated orders)")
        else:
            logger.info("Binance client ready. Using: %s", self.base_url)

    def _get_timestamp(self):
        """Get current time in milliseconds (required by Binance API)."""
        return int(time.time() * 1000)

    def _create_signature(self, params):
        """
        Create HMAC-SHA256 signature for the request.
        Binance requires this to verify the request is from us.
        """
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _send_signed_request(self, method, endpoint, params):
        """
        Send a signed request to the Binance API.
        Adds timestamp and signature automatically.
        """
        url = self.base_url + endpoint

        # Add timestamp and signature
        params["timestamp"] = self._get_timestamp()
        params["signature"] = self._create_signature(params)

        logger.debug("Sending %s request to %s with params: %s", method, url, params)

        # Try to send the request
        try:
            if method.upper() == "POST":
                response = self.session.post(url, data=params, timeout=30)
            else:
                response = self.session.get(url, params=params, timeout=30)
        except requests.exceptions.ConnectionError as e:
            logger.error("Could not connect to Binance API! %s", e)
            raise ConnectionError("Could not connect to Binance. Check your internet connection.")
        except requests.exceptions.Timeout:
            logger.error("Request timed out!")
            raise ConnectionError("Request to Binance timed out. Try again later.")
        except requests.exceptions.RequestException as e:
            logger.error("Request failed: %s", e)
            raise ConnectionError(f"Request to Binance failed: {e}")

        # Parse the response
        data = response.json()
        logger.debug("Response (status %s): %s", response.status_code, data)

        # Check for errors
        if response.status_code != 200:
            error_code = data.get("code", -1)
            error_msg = data.get("msg", "Unknown error")
            logger.error("API error: %s (code: %s)", error_msg, error_code)
            raise BinanceAPIError(response.status_code, error_code, error_msg)

        return data

    def _simulate_order(self, params):
        """
        Simulate an order response for demo mode.
        Returns a response that looks like a real Binance API response.
        """
        symbol = params["symbol"]
        side = params["side"]
        order_type = params["type"]
        quantity = params["quantity"]
        timestamp = self._get_timestamp()
        order_id = random.randint(1000000, 9999999)

        # Get a realistic price for the symbol
        price = self._get_current_price(symbol)

        response = {
            "orderId": order_id,
            "symbol": symbol,
            "status": "FILLED" if order_type == "MARKET" else "NEW",
            "clientOrderId": f"demo_{timestamp}",
            "price": params.get("price", "0.00"),
            "avgPrice": str(price),
            "origQty": str(quantity),
            "executedQty": str(quantity) if order_type == "MARKET" else "0",
            "cumQuote": str(round(float(quantity) * price, 2)),
            "timeInForce": params.get("timeInForce", "GTC"),
            "type": order_type,
            "side": side,
            "updateTime": timestamp,
        }

        logger.info("DEMO order response: %s", response)
        return response

    def _get_current_price(self, symbol):
        """Get the current price from the Binance public API (no auth needed)."""
        try:
            url = f"{self.base_url}/fapi/v1/ticker/price"
            r = requests.get(url, params={"symbol": symbol}, timeout=10)
            if r.status_code == 200:
                return float(r.json()["price"])
        except Exception:
            pass

        # Fallback prices if API fails
        fallback = {"BTCUSDT": 87500.00, "ETHUSDT": 1620.00, "BNBUSDT": 605.00}
        return fallback.get(symbol, 100.00)

    def place_order(self, symbol, side, order_type, quantity, price=None, time_in_force=None):
        """
        Place an order on Binance Futures Testnet.

        symbol: Trading pair like 'BTCUSDT'
        side: 'BUY' or 'SELL'
        order_type: 'MARKET' or 'LIMIT'
        quantity: How much to buy/sell
        price: Price for LIMIT orders (not needed for MARKET)
        time_in_force: How long the order stays active (default: GTC)
        """
        # Build the order parameters
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
        }

        # Add price and timeInForce for LIMIT orders
        if order_type == "LIMIT":
            if price is None:
                raise ValueError("Price is required for LIMIT orders!")
            params["price"] = str(price)
            params["timeInForce"] = time_in_force or "GTC"

        logger.info("Placing %s %s order for %s (qty: %s, price: %s)",
                     order_type, side, symbol, quantity, price)

        # Use demo mode or real API
        if self.demo:
            return self._simulate_order(params)
        else:
            return self._send_signed_request("POST", "/fapi/v1/order", params)

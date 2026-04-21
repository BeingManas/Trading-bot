"""
Order placement functions.
These functions validate user input and then use the client to place orders.
"""

import logging

from bot.client import BinanceClient
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_quantity,
    validate_price,
)

logger = logging.getLogger("trading_bot.orders")


def format_order_response(response):
    """Pick out the important fields from the API response."""
    return {
        "orderId": response.get("orderId"),
        "symbol": response.get("symbol"),
        "side": response.get("side"),
        "type": response.get("type"),
        "status": response.get("status"),
        "quantity": response.get("origQty"),
        "executedQty": response.get("executedQty"),
        "price": response.get("price", "N/A"),
        "avgPrice": response.get("avgPrice", "N/A"),
    }


def place_market_order(client, symbol, side, quantity):
    """
    Place a MARKET order (buys/sells immediately at current price).

    client: BinanceClient instance
    symbol: Trading pair like 'BTCUSDT'
    side: 'BUY' or 'SELL'
    quantity: How much to buy/sell
    """
    # Validate all inputs first
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    quantity = validate_quantity(quantity)

    logger.info("Placing MARKET %s order for %s, quantity: %s", side, symbol, quantity)

    # Place the order
    raw_response = client.place_order(
        symbol=symbol,
        side=side,
        order_type="MARKET",
        quantity=quantity,
    )

    # Format and return the response
    result = format_order_response(raw_response)
    logger.info("Order result: %s", result)
    return result


def place_limit_order(client, symbol, side, quantity, price):
    """
    Place a LIMIT order (buys/sells at a specific price).

    client: BinanceClient instance
    symbol: Trading pair like 'BTCUSDT'
    side: 'BUY' or 'SELL'
    quantity: How much to buy/sell
    price: The price you want to buy/sell at
    """
    # Validate all inputs first
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    quantity = validate_quantity(quantity)
    price = validate_price(price, "LIMIT")

    logger.info("Placing LIMIT %s order for %s, quantity: %s, price: %s",
                side, symbol, quantity, price)

    # Place the order
    raw_response = client.place_order(
        symbol=symbol,
        side=side,
        order_type="LIMIT",
        quantity=quantity,
        price=price,
    )

    # Format and return the response
    result = format_order_response(raw_response)
    logger.info("Order result: %s", result)
    return result

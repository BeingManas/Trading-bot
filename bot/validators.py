"""
Simple input validation functions.
Each function checks if the input is valid and raises an error if not.
"""


def validate_symbol(symbol):
    """Check that symbol is not empty and only has letters/numbers."""
    if not symbol or not symbol.strip():
        raise ValueError("Symbol cannot be empty.")
    symbol = symbol.strip().upper()
    if not symbol.isalnum():
        raise ValueError(f"Symbol must only contain letters and numbers. Got: '{symbol}'")
    return symbol


def validate_side(side):
    """Check that side is either BUY or SELL."""
    if not side:
        raise ValueError("Side cannot be empty.")
    side = side.strip().upper()
    if side not in ("BUY", "SELL"):
        raise ValueError(f"Side must be BUY or SELL. Got: '{side}'")
    return side


def validate_order_type(order_type):
    """Check that order type is either MARKET or LIMIT."""
    if not order_type:
        raise ValueError("Order type cannot be empty.")
    order_type = order_type.strip().upper()
    if order_type not in ("MARKET", "LIMIT"):
        raise ValueError(f"Order type must be MARKET or LIMIT. Got: '{order_type}'")
    return order_type


def validate_quantity(quantity):
    """Check that quantity is a positive number."""
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        raise ValueError(f"Quantity must be a number. Got: '{quantity}'")
    if quantity <= 0:
        raise ValueError(f"Quantity must be greater than 0. Got: {quantity}")
    return quantity


def validate_price(price, order_type):
    """
    Check the price value.
    - For MARKET orders: price is not needed, return None
    - For LIMIT orders: price must be a positive number
    """
    if order_type.upper() == "MARKET":
        return None

    if price is None:
        raise ValueError("Price is required for LIMIT orders.")
    try:
        price = float(price)
    except (TypeError, ValueError):
        raise ValueError(f"Price must be a number. Got: '{price}'")
    if price <= 0:
        raise ValueError(f"Price must be greater than 0. Got: {price}")
    return price

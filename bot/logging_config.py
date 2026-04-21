"""
Sets up logging so we can track what the bot does.
Logs go to both the console and a file.
"""

import logging
import os


def setup_logging():
    """Set up logging to console and file."""

    # Create our logger
    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.DEBUG)

    # Don't add handlers twice if called again
    if logger.handlers:
        return logger

    # Format: timestamp | level | message
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler 1: Print to console (INFO and above)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # Handler 2: Save to file (everything, including DEBUG)
    # Wrapped in try/except for serverless environments (e.g. Vercel)
    try:
        log_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        os.makedirs(log_folder, exist_ok=True)
        log_file = os.path.join(log_folder, "trading_bot.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info("Logging started. Log file: %s", log_file)
    except (OSError, PermissionError):
        logger.info("Logging started (console only — file logging unavailable)")

    return logger


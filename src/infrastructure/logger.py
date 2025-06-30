import logging
import sys


def setup_logger():
    """
    Configures and returns a standardized logger.
    """
    logger = logging.getLogger("data_engine")
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if the function is called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create a handler to output logs to the console
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    # Create a formatter and set it for the handler
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    return logger


# Create a default logger instance to be imported by other modules
log = setup_logger() 
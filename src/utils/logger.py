import logging
import sys
import colorlog


def setup_logger():
    # Create a custom formatter that includes file and line information with colors
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    # Create a handler for console output
    console_handler = colorlog.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.stream.reconfigure(encoding="utf-8")  # Ensure utf-8 encoding

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # Remove any existing handlers to avoid duplicate logs
    for handler in root_logger.handlers[:]:
        if not isinstance(handler, colorlog.StreamHandler):
            root_logger.removeHandler(handler)

    return root_logger


# Create a singleton logger instance
logger = setup_logger()


def get_function_logger(function_name: str) -> logging.Logger:
    """
    Get a logger instance for an Azure Function with proper context
    """
    function_logger = logging.getLogger(function_name)
    function_logger.setLevel(logging.INFO)
    return function_logger

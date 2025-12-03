"""
Logging configuration
"""
import logging
import sys
from pathlib import Path
from rich.logging import RichHandler
from config.settings import settings

def setup_logger(name: str = "screenshot_validator") -> logging.Logger:
    """
    Setup logger with Rich handler for beautiful console output
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Rich handler for console output
    rich_handler = RichHandler(
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        markup=True
    )
    rich_handler.setFormatter(
        logging.Formatter(
            "%(message)s",
            datefmt="[%X]"
        )
    )
    logger.addHandler(rich_handler)
    
    # File handler for persistent logging
    log_file = settings.output_dir / "validation.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    )
    logger.addHandler(file_handler)
    
    return logger

# Default logger instance
logger = setup_logger()

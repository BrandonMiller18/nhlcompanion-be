import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging() -> None:
    """
    Configure application-wide logging with rotating file handler.
    
    - Logs ERROR level and above to rotating files (10MB per file, 5 backups)
    - Logs ERROR level to console
    - Log files stored in services/db/logs/ directory
    - Format includes timestamp, module, level, function name, and message
    """
    # Determine the logs directory path
    current_file = Path(__file__)
    db_dir = current_file.parent.parent  # services/db/
    logs_dir = db_dir / "logs"
    
    # Create logs directory if it doesn't exist
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / "nhl_companion.log"
    
    # Define log format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Create formatter
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.ERROR)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create rotating file handler (10MB per file, keep 5 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Create console handler for ERROR level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given module name.
    
    Args:
        name: Usually __name__ from the calling module
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


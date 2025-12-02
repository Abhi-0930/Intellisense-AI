# app/core/logging.py
import logging
import os
from typing import Optional

LOG_FILE_PATH = "logs/app.log"

class TraceIdFilter(logging.Filter):
    """
    Injects trace_id into every log record so formatter can use it.
    """
    
    def __init__(self, trace_id: Optional[str] = None):
        super().__init__()
        self.trace_id = trace_id

    def filter(self, record):
        record.trace_id = getattr(record, "trace_id", "none")
        return True
    
def configure_logger() -> logging.Logger:
    """Create a centralized logger with console + file handlers."""

    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger("IntelliSenseAI")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Prevent double logging

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | trace_id=%(trace_id)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(TraceIdFilter())
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(LOG_FILE_PATH)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(TraceIdFilter())
    logger.addHandler(file_handler)

    return logger


# Global logger instance
logger = configure_logger()

def log_info(message: str, trace_id: Optional[str] = None):
    """Log info message with optional trace ID."""
    logger.info(message, extra={"trace_id": trace_id or "none"})


def log_error(message: str, trace_id: Optional[str] = None):
    """Log error message with optional trace ID."""
    logger.error(message, extra={"trace_id": trace_id or "none"})


def log_warning(message: str, trace_id: Optional[str] = None):
    """Log warning message with optional trace ID."""
    logger.warning(message, extra={"trace_id": trace_id or "none"})
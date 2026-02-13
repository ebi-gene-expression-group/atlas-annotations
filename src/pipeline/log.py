"""Logging utilities for atlas-annotations."""
import sys
from datetime import datetime
from typing import Any


def format_log_line(line: str) -> str:
    """Format a log line with timestamp."""
    now = datetime.now().strftime("%Y-%m-%d:%H:%M:%S")
    return f"{now}: {line}"


def write_to_stream(stream, message: Any) -> None:
    """Write a message to a stream with proper formatting."""
    if isinstance(message, str):
        stream.write(format_log_line(message) + "\n")
        stream.flush()
    elif isinstance(message, (list, tuple)):
        for item in message:
            write_to_stream(stream, item)
    elif isinstance(message, Exception):
        msg = str(message) if str(message) else repr(message)
        write_to_stream(stream, msg)
    else:
        write_to_stream(stream, str(message))


def log(message: Any) -> None:
    """Log a message to stdout."""
    write_to_stream(sys.stdout, message)


def err(message: Any) -> None:
    """Log an error message to stderr."""
    write_to_stream(sys.stderr, message)

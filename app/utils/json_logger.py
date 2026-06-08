"""
Structured JSON logging for RAG operations with request tracking.
Automatically correlates logs via unique request IDs.
"""

import json
import logging
import time
from typing import Any, Dict, Optional
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include request_id if available in extra fields
        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id

        # Include custom fields from extra dict
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class StructuredLogger:
    """Structured logger with request tracking support."""

    def __init__(self, name: str = "rag-assistant"):
        """Initialize structured logger."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Remove default handlers to avoid duplication
        self.logger.handlers.clear()

        # Add JSON handler
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

    def log_with_request_id(
        self,
        level: str,
        message: str,
        request_id: str,
        extra_fields: Optional[Dict[str, Any]] = None,
    ):
        """Log message with request ID correlation."""
        log_record = logging.LogRecord(
            name=self.logger.name,
            level=getattr(logging, level.upper(), logging.INFO),
            pathname="",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None,
        )
        log_record.request_id = request_id
        log_record.extra_fields = extra_fields or {}

        self.logger.handle(log_record)

    def debug(self, message: str, request_id: str = "", **extra):
        """Log debug message."""
        self.log_with_request_id("DEBUG", message, request_id, extra)

    def info(self, message: str, request_id: str = "", **extra):
        """Log info message."""
        self.log_with_request_id("INFO", message, request_id, extra)

    def warning(self, message: str, request_id: str = "", **extra):
        """Log warning message."""
        self.log_with_request_id("WARNING", message, request_id, extra)

    def error(self, message: str, request_id: str = "", **extra):
        """Log error message."""
        self.log_with_request_id("ERROR", message, request_id, extra)


class ExecutionLogger:
    """High-level execution logger for tracking pipeline stages."""

    def __init__(self, request_id: str):
        """Initialize execution logger."""
        self.request_id = request_id
        self.logger = StructuredLogger("rag-pipeline")
        self.logs: list[Dict[str, Any]] = []
        self.stage_timers: Dict[str, float] = {}

    def start_stage(self, stage_name: str):
        """Mark the start of a processing stage."""
        self.stage_timers[stage_name] = time.perf_counter()
        self.logger.info(
            f"Starting stage: {stage_name}",
            request_id=self.request_id,
            stage=stage_name,
        )

    def end_stage(self, stage_name: str, status: str = "success", **extra):
        """Mark the end of a processing stage."""
        if stage_name not in self.stage_timers:
            self.logger.warning(
                f"Stage {stage_name} end called without start",
                request_id=self.request_id,
            )
            return

        duration_ms = (time.perf_counter() - self.stage_timers[stage_name]) * 1000
        del self.stage_timers[stage_name]

        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": self.request_id,
            "stage": stage_name,
            "duration_ms": round(duration_ms, 2),
            "status": status,
            **extra,
        }
        self.logs.append(log_entry)

        self.logger.info(
            f"Completed stage: {stage_name}",
            request_id=self.request_id,
            stage=stage_name,
            duration_ms=round(duration_ms, 2),
            status=status,
        )

    def log_event(self, event_name: str, **extra):
        """Log a custom event."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": self.request_id,
            "event": event_name,
            **extra,
        }
        self.logs.append(log_entry)

        self.logger.info(
            f"Event: {event_name}",
            request_id=self.request_id,
            **extra,
        )

    def get_logs(self) -> list[Dict[str, Any]]:
        """Get all collected logs."""
        return self.logs

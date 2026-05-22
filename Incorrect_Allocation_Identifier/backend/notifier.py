"""
notifier.py — RM Team Notification

Sends an alert to the RM team when exceptions are detected.
Only calls the approved notification endpoint (configurable via .env).
If endpoint is not configured, logs a warning and skips silently.
"""

import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class Notifier:
    """Handles RM team notifications when exceptions are detected."""

    def __init__(self, notification_url: str = ""):
        self.notification_url = notification_url.strip() if notification_url else ""

    def notify(self, exception_count: int, run_timestamp: str, report_path: str, run_id: int = None):
        """
        Send notification to RM team about detected exceptions.

        Args:
            exception_count: Number of exceptions found
            run_timestamp: Timestamp of the pipeline run
            report_path: Path to the generated Excel report
            run_id: Optional database run ID for reference
        """
        if exception_count == 0:
            logger.info("No exceptions found. RM Team notification skipped.")
            return

        if not self.notification_url:
            logger.warning(
                f"RM Notification URL not configured. "
                f"Skipping notification for {exception_count} exceptions. "
                f"Set RM_NOTIFICATION_URL in .env to enable."
            )
            # Still log the notification payload for audit trail
            self._log_notification(exception_count, run_timestamp, report_path, run_id)
            return

        payload = self._build_payload(exception_count, run_timestamp, report_path, run_id)

        try:
            import httpx
            response = httpx.post(
                self.notification_url,
                json=payload,
                timeout=30.0,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            logger.info(
                f"RM Notification sent successfully to {self.notification_url}. "
                f"Status: {response.status_code}"
            )
        except ImportError:
            logger.warning(
                "httpx not installed. Notification skipped. "
                "Install with: pip install httpx"
            )
            self._log_notification(exception_count, run_timestamp, report_path, run_id)
        except Exception as e:
            logger.error(f"Failed to send RM notification: {e}")
            self._log_notification(exception_count, run_timestamp, report_path, run_id)

    def _build_payload(self, exception_count: int, run_timestamp: str, report_path: str, run_id: int = None) -> dict:
        """Build the notification payload."""
        return {
            "agent": "IAI — Incorrect Allocation Identifier",
            "event": "exceptions_detected",
            "run_id": run_id,
            "run_timestamp": run_timestamp,
            "exception_count": exception_count,
            "report_path": report_path,
            "message": (
                f"IAI Agent detected {exception_count} allocation exception(s) "
                f"during the run at {run_timestamp}. "
                f"Exception report is available at: {report_path}"
            ),
            "sent_at": datetime.now().isoformat(),
        }

    def _log_notification(self, exception_count: int, run_timestamp: str, report_path: str, run_id: int = None):
        """Log the notification payload for audit trail when endpoint is unavailable."""
        payload = self._build_payload(exception_count, run_timestamp, report_path, run_id)
        logger.info(
            f"NOTIFICATION (logged): {json.dumps(payload, indent=2)}"
        )

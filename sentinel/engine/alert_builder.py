from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sentinel.engine.rules_engine import RuleMatchResult


class AlertBuilder:
    """
    Builds alerts strictly from metadata.
    Never copies unknown fields, never includes GMP values, never echoes free text.
    """

    def __init__(self, audit_logger: Any):
        self._audit = audit_logger

    @staticmethod
    def _now_utc_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _new_alert_id() -> str:
        # Stable length, low collision risk
        return f"ALT-{uuid.uuid4().hex[:24]}"

    def build_alert(self, event: Dict[str, Any], match: RuleMatchResult) -> Dict[str, Any]:
        event_id = str(event.get("event_id", "")) or None

        alert: Dict[str, Any] = {
            "alert_id": self._new_alert_id(),
            "created_at": self._now_utc_iso(),
            "status": "NEW",
            "severity": match.severity,
            "risk_code": match.risk_code,
            "source_system": event.get("source_system"),
            "site": event.get("site"),
            "area": event.get("area"),
            "product_id": event.get("product_id"),
            "dbr_template_id": event.get("dbr_template_id"),
            "dbr_template_version": event.get("dbr_template_version"),
            "step_code": event.get("step_code"),
            "section_code": event.get("section_code"),
            "rule_id": match.rule_id,
            "rule_version": match.rule_version,
        }

        # Optional metadata fields (still safe)
        for optional_key in [
            "suite",
            "line",
            "page_number",
            "batch_token",
            "operator_role",
            "operator_token",
        ]:
            if optional_key in event and event.get(optional_key) is not None:
                alert[optional_key] = event.get(optional_key)

        if event_id:
            alert["event_refs"] = [event_id]

        if match.recommended_action:
            # bounded already in schema; keep as-is
            alert["recommended_action"] = match.recommended_action

        # NOTE: closure_category and closure_notes are optional and not set here.
        # They are only set when an alert is CLOSED.

        self._audit.log_alert_built(
            event_id=event_id,
            alert_id=alert.get("alert_id"),
            rule_id=match.rule_id,
            risk_code=match.risk_code,
            severity=match.severity,
        )
        return alert

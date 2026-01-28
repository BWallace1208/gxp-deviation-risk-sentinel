from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, List


class AuditLogger:
    """
    Append-only JSONL audit logger.

    HARDENING RULES:
      - Never write event payload bodies to disk here.
      - Only minimal metadata for rejects, accepts, rule evaluation, and alert outcomes.
      - Each audit record is a single JSON object line (JSONL).
    """

    def __init__(self, audit_log_path: Path):
        self.path = audit_log_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    @staticmethod
    def _now_utc_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _append(self, record: Dict[str, Any]) -> None:
        # Append-only JSONL; keep it atomic-ish
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")

    # -----------------------------
    # Phase 3.1: Ingestion logging
    # -----------------------------

    def log_rejection(self, rejection: Any) -> None:
        """
        rejection must support .to_dict() returning minimal metadata only.
        """
        rec = {
            "record_type": "INGEST_REJECT",
            "logged_at": self._now_utc_iso(),
            **rejection.to_dict(),
        }
        self._append(rec)

    def log_ingest_accept(
        self,
        event_id: Optional[str],
        source_system: Optional[str],
        event_timestamp: Optional[str],
        received_at: str,
        schema_version: str,
        tripwire_version: str,
    ) -> None:
        rec = {
            "record_type": "INGEST_ACCEPT",
            "logged_at": self._now_utc_iso(),
            "event_id": event_id,
            "source_system": source_system,
            "event_timestamp": event_timestamp,
            "received_at": received_at,
            "schema_version": schema_version,
            "tripwire_version": tripwire_version,
        }
        self._append(rec)

    # -----------------------------
    # Phase 3.2: Rules + alerts
    # -----------------------------

    def log_rules_loaded(self, ruleset_name: str, ruleset_version: str, rules_count: int) -> None:
        self._append(
            {
                "record_type": "RULES_LOADED",
                "logged_at": self._now_utc_iso(),
                "ruleset_name": ruleset_name,
                "ruleset_version": ruleset_version,
                "rules_count": rules_count,
            }
        )

    def log_rule_evaluation_start(
        self,
        event_id: Optional[str],
        event_type: Optional[str],
        ruleset_name: str,
        ruleset_version: str,
    ) -> None:
        self._append(
            {
                "record_type": "RULE_EVAL_START",
                "logged_at": self._now_utc_iso(),
                "event_id": event_id,
                "event_type": event_type,
                "ruleset_name": ruleset_name,
                "ruleset_version": ruleset_version,
            }
        )

    def log_rule_skipped(
        self,
        event_id: Optional[str],
        rule_id: Optional[str],
        rule_version: Optional[str],
        reason: str,
    ) -> None:
        self._append(
            {
                "record_type": "RULE_SKIPPED",
                "logged_at": self._now_utc_iso(),
                "event_id": event_id,
                "rule_id": rule_id,
                "rule_version": rule_version,
                "reason": reason,
            }
        )

    def log_rule_match(
        self,
        event_id: Optional[str],
        event_type: Optional[str],
        rule_id: Optional[str],
        rule_version: Optional[str],
        risk_code: Optional[str],
        severity: Optional[str],
    ) -> None:
        self._append(
            {
                "record_type": "RULE_MATCH",
                "logged_at": self._now_utc_iso(),
                "event_id": event_id,
                "event_type": event_type,
                "rule_id": rule_id,
                "rule_version": rule_version,
                "risk_code": risk_code,
                "severity": severity,
            }
        )

    def log_rule_no_match(
        self,
        event_id: Optional[str],
        event_type: Optional[str],
        ruleset_name: str,
        ruleset_version: str,
    ) -> None:
        self._append(
            {
                "record_type": "RULE_NO_MATCH",
                "logged_at": self._now_utc_iso(),
                "event_id": event_id,
                "event_type": event_type,
                "ruleset_name": ruleset_name,
                "ruleset_version": ruleset_version,
            }
        )

    def log_alert_built(
        self,
        event_id: Optional[str],
        alert_id: Optional[str],
        rule_id: Optional[str],
        risk_code: Optional[str],
        severity: Optional[str],
    ) -> None:
        self._append(
            {
                "record_type": "ALERT_BUILT",
                "logged_at": self._now_utc_iso(),
                "event_id": event_id,
                "alert_id": alert_id,
                "rule_id": rule_id,
                "risk_code": risk_code,
                "severity": severity,
            }
        )

    def log_alert_persisted(
        self,
        alert_id: Optional[str],
        persisted_at: str,
        store_type: str,
        store_path: str,
    ) -> None:
        self._append(
            {
                "record_type": "ALERT_PERSISTED",
                "logged_at": self._now_utc_iso(),
                "alert_id": alert_id,
                "persisted_at": persisted_at,
                "store_type": store_type,
                "store_path": store_path,
            }
        )

    # -----------------------------
    # Phase 3.3: Suppression
    # -----------------------------

    def log_alert_suppressed(
        self,
        event_id: Optional[str],
        rule_id: Optional[str],
        suppression_key: str,
        window_minutes: int,
        last_emitted_at: Optional[str],
    ) -> None:
        self._append(
            {
                "record_type": "ALERT_SUPPRESSED",
                "logged_at": self._now_utc_iso(),
                "event_id": event_id,
                "rule_id": rule_id,
                "suppression_key": suppression_key,
                "window_minutes": window_minutes,
                "last_emitted_at": last_emitted_at,
            }
        )

    # -----------------------------
    # Phase 3.4: Routing enforcement
    # -----------------------------

    def log_routing_applied(
        self,
        event_id: Optional[str],
        rule_id: Optional[str],
        consumers: List[str],
        policy_version: str,
    ) -> None:
        self._append(
            {
                "record_type": "ROUTING_APPLIED",
                "logged_at": self._now_utc_iso(),
                "event_id": event_id,
                "rule_id": rule_id,
                "consumers": consumers,
                "policy_version": policy_version,
            }
        )

    # -----------------------------
    # Phase 3.5: Correlation
    # -----------------------------

    def log_correlation_hit(
        self,
        event_id: Optional[str],
        rule_id: Optional[str],
        matched_event_ids: List[str],
        window_minutes: int,
    ) -> None:
        self._append(
            {
                "record_type": "CORRELATION_HIT",
                "logged_at": self._now_utc_iso(),
                "event_id": event_id,
                "rule_id": rule_id,
                "matched_event_ids": matched_event_ids,
                "window_minutes": window_minutes,
            }
        )

    def log_correlation_pruned(self, max_age_minutes: int) -> None:
        """
        Optional breadcrumb to show periodic pruning is happening.
        """
        self._append(
            {
                "record_type": "CORRELATION_PRUNE",
                "logged_at": self._now_utc_iso(),
                "max_age_minutes": max_age_minutes,
            }
        )

    # -----------------------------
    # Internal errors (minimal)
    # -----------------------------

    def log_internal_error(
        self,
        component: str,
        error_code: str,
        error_text: str,
        event_id: Optional[str] = None,
        rule_id: Optional[str] = None,
        alert_id: Optional[str] = None,
    ) -> None:
        """
        Minimal internal error record.
        Do not log payloads or raw objects.
        """
        self._append(
            {
                "record_type": "INTERNAL_ERROR",
                "logged_at": self._now_utc_iso(),
                "component": component,
                "error_code": error_code,
                "error_text": error_text,
                "event_id": event_id,
                "rule_id": rule_id,
                "alert_id": alert_id,
            }
        )

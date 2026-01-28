from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class AlertStore:
    """
    Append-only alert store (JSONL).
    v0.1 uses file-based storage intentionally (low complexity, easy to audit).
    """

    def __init__(self, alerts_path: Path, audit_logger: Any):
        self.path = alerts_path
        self._audit = audit_logger
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    @staticmethod
    def _now_utc_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def append(self, alert: Dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(alert, sort_keys=True) + "\n")

        self._audit.log_alert_persisted(
            alert_id=str(alert.get("alert_id", "")) or None,
            persisted_at=self._now_utc_iso(),
            store_type="JSONL",
            store_path=str(self.path),
        )

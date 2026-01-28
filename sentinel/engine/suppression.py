from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class SuppressionDecision:
    suppressed: bool
    suppression_key: str
    window_minutes: int
    last_emitted_at: Optional[str] = None
    reason: Optional[str] = None


class SuppressionStore:
    """
    Simple, auditable suppression state store.
    Stores only:
      suppression_key -> last_emitted_at (UTC ISO)
    No payloads. No GMP.
    """

    def __init__(self, state_path: Path):
        self.path = state_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"version": "0.1", "state": {}})

    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _parse_iso(ts: str) -> datetime:
        # python 3.14 supports fromisoformat with timezone offsets
        return datetime.fromisoformat(ts)

    def _read(self) -> Dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, obj: Dict[str, Any]) -> None:
        self.path.write_text(json.dumps(obj, sort_keys=True, indent=2), encoding="utf-8")

    def check_and_update(self, suppression_key: str, window_minutes: int) -> SuppressionDecision:
        doc = self._read()
        state: Dict[str, str] = doc.get("state", {}) or {}

        now = self._now_utc()

        last = state.get(suppression_key)
        if last:
            try:
                last_dt = self._parse_iso(last)
                delta_min = (now - last_dt).total_seconds() / 60.0
                if delta_min < float(window_minutes):
                    return SuppressionDecision(
                        suppressed=True,
                        suppression_key=suppression_key,
                        window_minutes=window_minutes,
                        last_emitted_at=last,
                        reason="WITHIN_WINDOW",
                    )
            except Exception:
                # If state is corrupted, fail open but reset for auditability.
                pass

        # Not suppressed -> update last emitted
        state[suppression_key] = now.isoformat()
        doc["state"] = state
        self._write(doc)

        return SuppressionDecision(
            suppressed=False,
            suppression_key=suppression_key,
            window_minutes=window_minutes,
            last_emitted_at=state[suppression_key],
            reason="EMIT_ALLOWED",
        )

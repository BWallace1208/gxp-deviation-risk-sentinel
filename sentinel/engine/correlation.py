from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class CorrelationHit:
    rule_id: str
    rule_version: str
    matched_event_ids: List[str]
    window_minutes: int


class CorrelationStore:
    """
    Stores minimal correlation state (metadata-only):

      group_key -> list[
        {
          "event_id": str,
          "event_type": str,
          "event_timestamp": str (UTC ISO),
          "batch_token": Optional[str]
        }
      ]

    HARDENING:
      - No payload bodies
      - No GMP values (no quantities, temps, setpoints, free text narratives)
      - batch_token is treated as a non-sensitive surrogate/opaque token
      - Atomic writes (temp + fsync + replace) to prevent corrupted JSON on crash/interrupt
      - Safe read: auto-recovers if file is empty/corrupt
    """

    VERSION = "0.1"

    def __init__(self, state_path: Path):
        self.path = state_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write_atomic(self._empty_doc())

        # If it exists but is corrupt/empty, recover immediately
        _ = self._read_safe(recover=True)

    @staticmethod
    def _empty_doc() -> Dict[str, Any]:
        return {"version": CorrelationStore.VERSION, "groups": {}}

    @staticmethod
    def _parse_iso(ts: str) -> datetime:
        # Accept "Z" suffix
        s = (ts or "").strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)

    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(timezone.utc)

    def _read_safe(self, recover: bool = True) -> Dict[str, Any]:
        """
        Read JSON state. If unreadable and recover=True, rewrite a clean doc.
        """
        try:
            raw = self.path.read_text(encoding="utf-8")
            if not raw.strip():
                raise ValueError("state file empty")
            doc = json.loads(raw)
            if not isinstance(doc, dict):
                raise ValueError("state root is not an object")
            if "groups" not in doc or not isinstance(doc.get("groups"), dict):
                raise ValueError("missing/invalid 'groups'")
            if "version" not in doc:
                doc["version"] = self.VERSION
            return doc
        except Exception:
            if not recover:
                raise
            clean = self._empty_doc()
            self._write_atomic(clean)
            return clean

    def _write_atomic(self, obj: Dict[str, Any]) -> None:
        """
        Atomic write:
          - write to temp file in same directory
          - flush + fsync
          - replace target
        """
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        data = json.dumps(obj, sort_keys=True, indent=2)

        with tmp_path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())

        # Atomic replace on same filesystem
        os.replace(tmp_path, self.path)

    def add_event(
        self,
        group_key: str,
        event_id: str,
        event_type: str,
        event_timestamp: str,
        batch_token: Optional[str] = None,
    ) -> None:
        doc = self._read_safe(recover=True)
        groups: Dict[str, List[Dict[str, Any]]] = doc.get("groups", {}) or {}

        gk = str(group_key or "").strip()
        if not gk:
            # If group key is empty, do nothing (keeps state sane)
            return

        lst = groups.get(gk, [])
        if not isinstance(lst, list):
            lst = []

        # Normalize timestamp (keep ISO string)
        ts = str(event_timestamp or "").strip()
        if not ts:
            ts = self._now_utc().isoformat()

        record = {
            "event_id": str(event_id),
            "event_type": str(event_type),
            "event_timestamp": ts,
            "batch_token": str(batch_token) if batch_token else None,
        }

        lst.append(record)
        groups[gk] = lst
        doc["groups"] = groups
        doc["version"] = doc.get("version") or self.VERSION

        self._write_atomic(doc)

    def prune(self, max_age_minutes: int) -> None:
        doc = self._read_safe(recover=True)
        groups: Dict[str, List[Dict[str, Any]]] = doc.get("groups", {}) or {}

        cutoff = self._now_utc() - timedelta(minutes=int(max_age_minutes))
        new_groups: Dict[str, List[Dict[str, Any]]] = {}

        for gk, events in groups.items():
            if not isinstance(events, list):
                continue

            kept: List[Dict[str, Any]] = []
            for e in events:
                if not isinstance(e, dict):
                    continue
                try:
                    ts_raw = str(e.get("event_timestamp") or "").strip()
                    ts = self._parse_iso(ts_raw)
                    if ts >= cutoff:
                        kept.append(e)
                except Exception:
                    # Drop corrupted records to keep state clean
                    continue

            if kept:
                new_groups[str(gk)] = kept

        doc["groups"] = new_groups
        doc["version"] = doc.get("version") or self.VERSION
        self._write_atomic(doc)

    def get_group_events(self, group_key: str) -> List[Dict[str, Any]]:
        doc = self._read_safe(recover=True)
        groups: Dict[str, List[Dict[str, Any]]] = doc.get("groups", {}) or {}
        return groups.get(str(group_key), [])

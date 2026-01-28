from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import json
import yaml
from jsonschema import Draft202012Validator


JSONType = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


@dataclass(frozen=True)
class Rejection:
    rejection_reason_code: str
    rejection_reason_text: str
    event_id: Optional[str]
    source_system: Optional[str]
    event_timestamp: Optional[str]
    received_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rejection_reason_code": self.rejection_reason_code,
            "rejection_reason_text": self.rejection_reason_text,
            "event_id": self.event_id,
            "source_system": self.source_system,
            "event_timestamp": self.event_timestamp,
            "received_at": self.received_at,
        }


@dataclass
class IngestResult:
    accepted: bool
    accepted_event: Optional[Dict[str, Any]] = None
    rejection: Optional[Rejection] = None


class Ingestor:
    """
    Hardened ingestion gate:
      1) Strict schema validation (allow-list)
      2) Tripwire scan (deny-list) across keys + string values
      3) Minimal logging on reject (no payload persistence)
    """

    def __init__(self, event_schema_path: Path, tripwire_config_path: Path, audit_logger: Any):
        self._audit = audit_logger
        self._schema_validator = self._load_schema_validator(event_schema_path)
        self._tripwires = self._load_tripwires(tripwire_config_path)

    @staticmethod
    def _now_utc_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _load_schema_validator(schema_path: Path) -> Draft202012Validator:
        if not schema_path.exists():
            raise FileNotFoundError(f"Event schema not found: {schema_path}")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        return validator

    @staticmethod
    def _load_tripwires(path: Path) -> Dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(f"Tripwire config not found: {path}")
        cfg = json.loads(path.read_text(encoding="utf-8"))

        # Defensive parsing + compilation
        prohibited_exact = set(k.lower() for k in cfg.get("prohibited_keys_exact", []))
        key_patterns = [re.compile(p, flags=re.IGNORECASE) for p in cfg.get("prohibited_key_patterns_regex_i", [])]
        str_patterns = [re.compile(p, flags=re.IGNORECASE) for p in cfg.get("prohibited_string_patterns_regex_i", [])]

        logging_policy = cfg.get("logging_policy", {})
        log_payload_body_on_reject = bool(logging_policy.get("log_payload_body_on_reject", False))

        return {
            "version": cfg.get("version", "unknown"),
            "prohibited_exact": prohibited_exact,
            "key_patterns": key_patterns,
            "str_patterns": str_patterns,
            "log_payload_body_on_reject": log_payload_body_on_reject,  # should be False per policy
        }

    def process_event(self, event: Dict[str, Any]) -> IngestResult:
        received_at = self._now_utc_iso()

        # Pull minimal identifiers safely (do not assume schema validity)
        event_id = self._safe_str(event.get("event_id"))
        source_system = self._safe_str(event.get("source_system"))
        event_timestamp = self._safe_str(event.get("event_timestamp"))

        # 1) Schema validation (strict allow-list)
        schema_errors = sorted(self._schema_validator.iter_errors(event), key=lambda e: e.path)
        if schema_errors:
            msg = self._format_schema_error(schema_errors[0])
            rej = Rejection(
                rejection_reason_code="SCHEMA_INVALID",
                rejection_reason_text=msg,
                event_id=event_id,
                source_system=source_system,
                event_timestamp=event_timestamp,
                received_at=received_at,
            )
            self._audit.log_rejection(rej)
            return IngestResult(accepted=False, rejection=rej)

        # 2) Tripwire scan (deny-list)
        trip_hit = self._scan_tripwires(event)
        if trip_hit is not None:
            code, text = trip_hit
            rej = Rejection(
                rejection_reason_code=code,
                rejection_reason_text=text,
                event_id=event_id,
                source_system=source_system,
                event_timestamp=event_timestamp,
                received_at=received_at,
            )
            self._audit.log_rejection(rej)
            return IngestResult(accepted=False, rejection=rej)

        # 3) Accept — return normalized shape (light normalization now; deeper later)
        accepted_event = self._normalize_minimal(event)
        self._audit.log_ingest_accept(
            event_id=accepted_event.get("event_id"),
            source_system=accepted_event.get("source_system"),
            event_timestamp=accepted_event.get("event_timestamp"),
            received_at=received_at,
            schema_version="0.1",
            tripwire_version=self._tripwires["version"],
        )
        return IngestResult(accepted=True, accepted_event=accepted_event)

    @staticmethod
    def _safe_str(val: Any) -> Optional[str]:
        if val is None:
            return None
        if isinstance(val, str):
            return val
        return str(val)

    @staticmethod
    def _format_schema_error(err: Exception) -> str:
        # Keep short; do not echo full event
        loc = ".".join(str(p) for p in getattr(err, "path", [])) or "(root)"
        return f"Schema validation failed at {loc}: {getattr(err, 'message', 'invalid payload')}"

    def _normalize_minimal(self, event: Dict[str, Any]) -> Dict[str, Any]:
        # Minimal normalization only: trim whitespace in known string fields if present.
        # No field additions; no GMP data.
        out: Dict[str, Any] = dict(event)
        for k, v in list(out.items()):
            if isinstance(v, str):
                out[k] = v.strip()
        return out

    def _scan_tripwires(self, obj: JSONType) -> Optional[Tuple[str, str]]:
        """
        Returns (reason_code, reason_text) if prohibited data is detected, else None.
        Scans:
          - Keys: exact + regex patterns
          - String values: regex patterns (units/spec/narrative indicators)
        """
        prohibited_exact = self._tripwires["prohibited_exact"]
        key_patterns: List[re.Pattern] = self._tripwires["key_patterns"]
        str_patterns: List[re.Pattern] = self._tripwires["str_patterns"]

        def scan(node: JSONType, path: str) -> Optional[Tuple[str, str]]:
            if isinstance(node, dict):
                for key, val in node.items():
                    key_l = str(key).lower()

                    # Key exact match
                    if key_l in prohibited_exact:
                        return ("PROHIBITED_DATA_DETECTED", f"Prohibited key detected at {path}.{key}")

                    # Key regex patterns
                    for pat in key_patterns:
                        if pat.search(key_l):
                            return ("PROHIBITED_DATA_DETECTED", f"Prohibited key pattern detected at {path}.{key}")

                    # Recurse into value
                    hit = scan(val, f"{path}.{key}")
                    if hit:
                        return hit
                return None

            if isinstance(node, list):
                for i, item in enumerate(node):
                    hit = scan(item, f"{path}[{i}]")
                    if hit:
                        return hit
                return None

            if isinstance(node, str):
                # String content tripwires
                for pat in str_patterns:
                    if pat.search(node):
                        # Do NOT echo the string content back (avoid capturing GMP text)
                        return ("PROHIBITED_DATA_DETECTED", f"Prohibited content pattern detected at {path}")
                return None

            # primitives (int/float/bool/None) are allowed by schema; no action here
            return None

        return scan(obj, path="(root)")

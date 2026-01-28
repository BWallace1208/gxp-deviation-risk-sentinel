from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, List

from jsonschema import Draft202012Validator

from sentinel.engine.ingest import Ingestor, IngestResult
from sentinel.engine.audit import AuditLogger
from sentinel.engine.rules_engine import RulesEngine, RuleMatchResult
from sentinel.engine.alert_builder import AlertBuilder
from sentinel.engine.alert_store import AlertStore

from sentinel.engine.suppression import SuppressionStore
from sentinel.engine.routing import RoutingPolicy
from sentinel.engine.correlation import CorrelationStore


def load_json(path: Path) -> Dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
        obj = json.loads(raw)
    except Exception as e:
        raise RuntimeError(f"Failed to load JSON from {path}: {e}") from e
    if not isinstance(obj, dict):
        raise ValueError(f"Input must be a JSON object (dict). Got: {type(obj).__name__}")
    return obj


def load_json_obj(path: Path) -> Dict[str, Any]:
    """
    Strict JSON object loader for config artifacts.
    """
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"Config must be a JSON object: {path}")
    return obj


def load_schema_validator(schema_path: Path) -> Draft202012Validator:
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _resolve_base_dir() -> Path:
    """
    Prefer the repo checkout (current working directory) if it contains the expected
    sentinel layout. Otherwise fall back to installed package path.
    This prevents sweep/ingest from reading different storage dirs.
    """
    cwd = Path.cwd()
    sentinel_dir = cwd / "sentinel"
    if (sentinel_dir / "schemas").exists() and (sentinel_dir / "rules").exists():
        return sentinel_dir
    return Path(__file__).resolve().parent


def _safe_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def _parse_iso(ts: str) -> datetime:
    # accepts "Z" suffix; datetime.fromisoformat needs "+00:00"
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _suppression_key(event: Dict[str, Any], rule_id: Optional[str]) -> str:
    parts = [
        _safe_str(rule_id) or "",
        _safe_str(event.get("site")) or "",
        _safe_str(event.get("area")) or "",
        _safe_str(event.get("product_id")) or "",
        _safe_str(event.get("dbr_template_id")) or "",
        _safe_str(event.get("dbr_template_version")) or "",
        _safe_str(event.get("step_code")) or "",
        _safe_str(event.get("section_code")) or "",
        _safe_str(event.get("batch_token")) or "",
    ]
    return "|".join(parts)


def _make_group_key(event: Dict[str, Any]) -> str:
    return "|".join(
        [
            _safe_str(event.get("site")) or "",
            _safe_str(event.get("area")) or "",
            _safe_str(event.get("product_id")) or "",
            _safe_str(event.get("dbr_template_id")) or "",
            _safe_str(event.get("step_code")) or "",
            _safe_str(event.get("section_code")) or "",
        ]
    )


def _store_correlation_event(correlation_store: CorrelationStore, event: Dict[str, Any]) -> None:
    correlation_store.add_event(
        group_key=_make_group_key(event),
        event_id=_safe_str(event.get("event_id")) or "UNKNOWN",
        event_type=_safe_str(event.get("event_type")) or "UNKNOWN",
        event_timestamp=_safe_str(event.get("event_timestamp")) or _now_utc_iso(),
        batch_token=_safe_str(event.get("batch_token")),
    )


def _sweep_timeouts(
    audit: AuditLogger,
    sweep_cfg_path: Path,
    routing_policy: RoutingPolicy,
    suppression_store: SuppressionStore,
    correlation_store: CorrelationStore,
    alert_builder: AlertBuilder,
    alert_store: AlertStore,
    alert_validator: Draft202012Validator,
) -> int:
    """
    Sweep correlation state and emit timeout alerts for STEP_OPENED events that have
    not seen a matching STEP_COMPLETED (same batch_token, same group) within threshold.

    HARDENING:
      - Does NOT introspect RulesEngine internals (no private _rules_doc dependency).
      - Uses a controlled, vendor-neutral config artifact: config/sweep_timeouts_v0_1.json
      - Metadata-only; no GMP values logged or persisted.
    """
    try:
        cfg = load_json_obj(sweep_cfg_path)
    except Exception as e:
        audit.log_internal_error(
            component="SWEEP",
            error_code="SWEEP_CONFIG_LOAD_FAILED",
            error_text=str(e),
        )
        print(f"SWEEP config load failed: {e}", file=sys.stderr)
        return 2

    if not bool(cfg.get("enabled", True)):
        print("SWEEP disabled by config.")
        return 0

    rule_id = _safe_str(cfg.get("rule_id")) or "R-002-STEP_TIMEOUT"
    rule_version = _safe_str(cfg.get("rule_version")) or "0.1"

    threshold_min = int(cfg.get("threshold_minutes", 60))
    pair_type = _safe_str(cfg.get("pair_with_event_type")) or "STEP_COMPLETED"

    out = cfg.get("output", {}) or {}
    risk_code = _safe_str(out.get("risk_code"))
    severity = _safe_str(out.get("severity"))
    recommended_action = _safe_str(out.get("recommended_action"))

    routing_cfg = cfg.get("routing", {}) or {}
    consumers_raw = routing_cfg.get("consumers", [])
    consumers = [str(x) for x in consumers_raw] if isinstance(consumers_raw, list) else []

    suppression_cfg = cfg.get("suppression", {}) or {}
    window_minutes = int(suppression_cfg.get("window_minutes", threshold_min))

    # Load raw correlation state from disk
    try:
        state = json.loads((correlation_store.path).read_text(encoding="utf-8"))
    except Exception as e:
        audit.log_internal_error(
            component="SWEEP",
            error_code="CORRELATION_STATE_READ_FAILED",
            error_text=str(e),
        )
        print("Correlation state unreadable.", file=sys.stderr)
        return 2

    groups = state.get("groups", {}) if isinstance(state, dict) else {}
    if not isinstance(groups, dict):
        print("Correlation state malformed.", file=sys.stderr)
        return 2

    emitted = 0
    now = datetime.now(timezone.utc)

    for _, events in groups.items():
        if not isinstance(events, list):
            continue

        # index completions by batch_token
        completions: Dict[str, List[datetime]] = {}
        for e in events:
            if not isinstance(e, dict):
                continue
            if _safe_str(e.get("event_type")) != pair_type:
                continue
            bt = _safe_str(e.get("batch_token"))
            if not bt:
                continue
            try:
                ts = _parse_iso(_safe_str(e.get("event_timestamp")) or _now_utc_iso())
            except Exception:
                continue
            completions.setdefault(bt, []).append(ts)

        # process openings
        for e in events:
            if not isinstance(e, dict):
                continue
            if _safe_str(e.get("event_type")) != "STEP_OPENED":
                continue
            bt = _safe_str(e.get("batch_token"))
            if not bt:
                continue

            try:
                opened_at = _parse_iso(_safe_str(e.get("event_timestamp")) or _now_utc_iso())
            except Exception:
                continue

            # Only consider truly overdue openings
            if opened_at + timedelta(minutes=threshold_min) > now:
                continue

            # Completion within [opened_at, opened_at + threshold] ?
            ok = False
            for cts in completions.get(bt, []):
                if opened_at <= cts <= opened_at + timedelta(minutes=threshold_min):
                    ok = True
                    break
            if ok:
                continue

            # Metadata-only synthetic event for alert building
            synthetic_event = dict(e)
            synthetic_event["event_id"] = _safe_str(e.get("event_id")) or f"SWEEP-{bt}-{int(opened_at.timestamp())}"
            synthetic_event["event_timestamp"] = (opened_at + timedelta(minutes=threshold_min)).isoformat()
            # NOTE: received_at is system-generated; not part of ingest schema
            synthetic_event.setdefault("source_system", "DBR")
            synthetic_event.setdefault("site", "UNKNOWN_SITE")
            synthetic_event.setdefault("area", "UNKNOWN_AREA")
            synthetic_event.setdefault("product_id", "UNKNOWN_PRODUCT")
            synthetic_event.setdefault("dbr_template_id", "UNKNOWN_TEMPLATE")
            synthetic_event.setdefault("dbr_template_version", "0.1")
            synthetic_event.setdefault("page_number", 1)
            synthetic_event.setdefault("step_code", "UNKNOWN_STEP")
            synthetic_event.setdefault("section_code", "UNKNOWN_SECTION")
            synthetic_event.setdefault("operator_role", "OPERATOR")
            synthetic_event.setdefault("operator_token", "UNKNOWN_OPERATOR")
            synthetic_event["received_at"] = _now_utc_iso()

            # Enforce routing allow-list
            try:
                routing = routing_policy.normalize(consumers)
                consumers_norm = routing.consumers
                audit.log_routing_applied(
                    _safe_str(synthetic_event.get("event_id")),
                    rule_id,
                    consumers_norm,
                    routing_policy.version,
                )
            except Exception as ex:
                audit.log_internal_error(
                    component="ROUTING_POLICY",
                    error_code="ROUTING_NOT_ALLOWED",
                    error_text=str(ex),
                    event_id=_safe_str(synthetic_event.get("event_id")),
                    rule_id=rule_id,
                )
                continue

            # Suppression check (sweep should not spam)
            key = _suppression_key(synthetic_event, rule_id)
            decision = suppression_store.check_and_update(suppression_key=key, window_minutes=int(window_minutes))
            if decision.suppressed:
                audit.log_alert_suppressed(
                    event_id=_safe_str(synthetic_event.get("event_id")),
                    rule_id=rule_id,
                    suppression_key=decision.suppression_key,
                    window_minutes=decision.window_minutes,
                    last_emitted_at=decision.last_emitted_at,
                )
                continue

            # Use RuleMatchResult to feed AlertBuilder
            match = RuleMatchResult(
                matched=True,
                rule_id=rule_id,
                rule_version=rule_version,
                risk_code=risk_code,
                severity=severity,
                recommended_action=recommended_action,
                routing_consumers=consumers_norm,
                suppression_window_minutes=int(window_minutes),
                correlation={"type": "STEP_TIMEOUT_SWEEP", "threshold_minutes": threshold_min},
                qa_escalation=None,
            )

            audit.log_correlation_hit(
                event_id=_safe_str(synthetic_event.get("event_id")),
                rule_id=rule_id,
                matched_event_ids=[_safe_str(synthetic_event.get("event_id")) or "UNKNOWN"],
                window_minutes=threshold_min,
            )

            alert_obj = alert_builder.build_alert(synthetic_event, match)

            errors = sorted(alert_validator.iter_errors(alert_obj), key=lambda er: er.path)
            if errors:
                loc = ".".join(str(p) for p in errors[0].path) or "(root)"
                msg = f"Alert schema validation failed at {loc}: {errors[0].message}"
                audit.log_internal_error(
                    component="ALERT_SCHEMA_VALIDATE",
                    error_code="ALERT_SCHEMA_INVALID",
                    error_text=msg,
                    event_id=_safe_str(synthetic_event.get("event_id")),
                    rule_id=rule_id,
                    alert_id=_safe_str(alert_obj.get("alert_id")),
                )
                continue

            alert_store.append(alert_obj)
            emitted += 1

    print(f"SWEEP COMPLETE ✅  emitted={emitted}")
    return 0


def main(argv: list[str]) -> int:
    """
    Usage:
      python -m sentinel.app <path_to_event.json>
      python -m sentinel.app --sweep-timeouts
    """
    base_dir = _resolve_base_dir()

    schemas_dir = base_dir / "schemas"
    rules_dir = base_dir / "rules"
    storage_dir = base_dir / "storage"
    config_dir = base_dir / "config"
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Print once so you can SEE where sweep is reading/writing
    print(f"[SENTINEL] base_dir={base_dir}")
    print(f"[SENTINEL] storage_dir={storage_dir}")

    audit_log_path = storage_dir / "audit_log.jsonl"
    alerts_path = storage_dir / "alerts.jsonl"

    audit = AuditLogger(audit_log_path)

    alert_validator = load_schema_validator(schemas_dir / "alert_schema_v0_1.json")
    rules_engine = RulesEngine(rules_path=rules_dir / "rules_v0_1.yaml", audit_logger=audit)

    alert_builder = AlertBuilder(audit_logger=audit)
    alert_store = AlertStore(alerts_path=alerts_path, audit_logger=audit)

    suppression_store = SuppressionStore(storage_dir / "suppression_state_v0_1.json")
    routing_policy = RoutingPolicy(config_dir / "consumers_allowlist_v0_1.json")
    correlation_store = CorrelationStore(storage_dir / "correlation_state_v0_1.json")

    # Sweep mode (config-driven; does not depend on RulesEngine internals)
    if len(argv) == 2 and argv[1] == "--sweep-timeouts":
        sweep_cfg_path = config_dir / "sweep_timeouts_v0_1.json"
        return _sweep_timeouts(
            audit=audit,
            sweep_cfg_path=sweep_cfg_path,
            routing_policy=routing_policy,
            suppression_store=suppression_store,
            correlation_store=correlation_store,
            alert_builder=alert_builder,
            alert_store=alert_store,
            alert_validator=alert_validator,
        )

    # Normal mode
    if len(argv) != 2:
        print(
            "Usage: python -m sentinel.app <path_to_event.json>  OR  python -m sentinel.app --sweep-timeouts",
            file=sys.stderr,
        )
        return 2

    event_path = Path(argv[1]).resolve()
    if not event_path.exists() or not event_path.is_file():
        print(f"Event file not found: {event_path}", file=sys.stderr)
        return 2

    ingestor = Ingestor(
        event_schema_path=schemas_dir / "event_schema_v0_1.json",
        tripwire_config_path=schemas_dir / "prohibited_fields_v0_1.json",
        audit_logger=audit,
    )

    event = load_json(event_path)

    ingest_result: IngestResult = ingestor.process_event(event)
    if not ingest_result.accepted or not ingest_result.accepted_event:
        print("REJECTED ❌")
        print(json.dumps(ingest_result.rejection.to_dict(), indent=2, sort_keys=True))
        return 1

    accepted_event = ingest_result.accepted_event
    print("ACCEPTED ✅")

    event_id = _safe_str(accepted_event.get("event_id"))

    # Correlation state: store minimal event record (including batch_token) and prune
    try:
        _store_correlation_event(correlation_store, accepted_event)
        correlation_store.prune(max_age_minutes=24 * 60)
        audit.log_correlation_pruned(max_age_minutes=24 * 60)
    except Exception as e:
        audit.log_internal_error(
            component="CORRELATION_STORE",
            error_code="CORRELATION_STORE_ERROR",
            error_text=str(e),
            event_id=event_id,
        )

    match_result: RuleMatchResult = rules_engine.evaluate(accepted_event)

    if not match_result.matched:
        print("NO ALERT 💤")
        return 0

    # Routing enforcement
    try:
        routing = routing_policy.normalize(match_result.routing_consumers)
        match_result.routing_consumers = routing.consumers
        audit.log_routing_applied(event_id, match_result.rule_id, routing.consumers, routing_policy.version)
    except Exception as e:
        audit.log_internal_error(
            component="ROUTING_POLICY",
            error_code="ROUTING_NOT_ALLOWED",
            error_text=str(e),
            event_id=event_id,
            rule_id=match_result.rule_id,
        )
        raise

    # Suppression
    window = match_result.suppression_window_minutes
    if window and int(window) > 0:
        key = _suppression_key(accepted_event, match_result.rule_id)
        decision = suppression_store.check_and_update(suppression_key=key, window_minutes=int(window))
        if decision.suppressed:
            audit.log_alert_suppressed(
                event_id=event_id,
                rule_id=match_result.rule_id,
                suppression_key=decision.suppression_key,
                window_minutes=decision.window_minutes,
                last_emitted_at=decision.last_emitted_at,
            )
            print("ALERT SUPPRESSED 🧱")
            return 0

    # Build and validate alert
    alert_obj = alert_builder.build_alert(accepted_event, match_result)

    errors = sorted(alert_validator.iter_errors(alert_obj), key=lambda e: e.path)
    if errors:
        loc = ".".join(str(p) for p in errors[0].path) or "(root)"
        msg = f"Alert schema validation failed at {loc}: {errors[0].message}"
        audit.log_internal_error(
            component="ALERT_SCHEMA_VALIDATE",
            error_code="ALERT_SCHEMA_INVALID",
            error_text=msg,
            event_id=event_id,
            rule_id=match_result.rule_id,
            alert_id=_safe_str(alert_obj.get("alert_id")),
        )
        raise RuntimeError(msg)

    alert_store.append(alert_obj)

    print("ALERT EMITTED 🚨")
    print(json.dumps(alert_obj, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

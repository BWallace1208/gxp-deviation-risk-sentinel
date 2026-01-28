from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class RuleMatchResult:
    matched: bool
    rule_id: Optional[str] = None
    rule_version: Optional[str] = None
    risk_code: Optional[str] = None
    severity: Optional[str] = None
    recommended_action: Optional[str] = None
    routing_consumers: Optional[List[str]] = None
    suppression_window_minutes: Optional[int] = None

    # NEW: pass-through configs for Phase 3.5
    correlation: Optional[Dict[str, Any]] = None
    qa_escalation: Optional[Dict[str, Any]] = None


class RulesEngine:
    """
    Deterministic, metadata-only rules evaluation.
    - Single-event rules match on event_type (+ optional exact conditions).
    - Correlation & QA escalation configs are returned for app-layer evaluation.
    """

    def __init__(self, rules_path: Path, audit_logger: Any):
        if not rules_path.exists():
            raise FileNotFoundError(f"Rules file not found: {rules_path}")
        self._audit = audit_logger
        self._rules_doc = self._load_rules(rules_path)

        self._ruleset_name = self._rules_doc.get("ruleset", {}).get("name", "unknown")
        self._ruleset_version = self._rules_doc.get("ruleset", {}).get("version", "unknown")
        self._defaults = self._rules_doc.get("defaults", {}) or {}
        self._rules = self._rules_doc.get("rules", []) or []

        self._audit.log_rules_loaded(
            ruleset_name=self._ruleset_name,
            ruleset_version=self._ruleset_version,
            rules_count=len(self._rules),
        )

    @staticmethod
    def _load_rules(path: Path) -> Dict[str, Any]:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(doc, dict):
            raise ValueError("Rules YAML must parse to a dict.")
        return doc

    def defaults(self) -> Dict[str, Any]:
        return self._defaults

    def evaluate(self, event: Dict[str, Any]) -> RuleMatchResult:
        event_id = str(event.get("event_id", "")) or None
        event_type = str(event.get("event_type", "")) or None

        self._audit.log_rule_evaluation_start(
            event_id=event_id,
            event_type=event_type,
            ruleset_name=self._ruleset_name,
            ruleset_version=self._ruleset_version,
        )

        for rule in self._rules:
            if not isinstance(rule, dict):
                continue
            if not bool(rule.get("enabled", False)):
                continue

            trigger = rule.get("trigger", {}) or {}
            if not isinstance(trigger, dict):
                continue

            if not self._trigger_matches(trigger, event):
                continue

            output = rule.get("output", {}) or {}
            routing = rule.get("routing", {}) or {}
            suppression = rule.get("suppression", {}) or {}

            consumers = None
            if isinstance(routing, dict) and isinstance(routing.get("consumers"), list):
                consumers = [str(x) for x in routing["consumers"]]

            window_minutes = None
            if isinstance(suppression, dict) and suppression.get("window_minutes") is not None:
                window_minutes = int(suppression["window_minutes"])

            res = RuleMatchResult(
                matched=True,
                rule_id=str(rule.get("rule_id", "")) or None,
                rule_version=str(rule.get("rule_version", "")) or None,
                risk_code=str(output.get("risk_code", "")) or None,
                severity=str(output.get("severity", "")) or None,
                recommended_action=str(output.get("recommended_action", "")) or None,
                routing_consumers=consumers,
                suppression_window_minutes=window_minutes,
                correlation=rule.get("correlation"),
                qa_escalation=rule.get("qa_escalation"),
            )

            self._audit.log_rule_match(
                event_id=event_id,
                event_type=event_type,
                rule_id=res.rule_id,
                rule_version=res.rule_version,
                risk_code=res.risk_code,
                severity=res.severity,
            )
            return res

        self._audit.log_rule_no_match(
            event_id=event_id,
            event_type=event_type,
            ruleset_name=self._ruleset_name,
            ruleset_version=self._ruleset_version,
        )
        return RuleMatchResult(matched=False)

    @staticmethod
    def _trigger_matches(trigger: Dict[str, Any], event: Dict[str, Any]) -> bool:
        et = event.get("event_type")

        any_of = trigger.get("event_type_any_of")
        single = trigger.get("event_type")

        if any_of is not None:
            if not isinstance(any_of, list):
                return False
            if et not in any_of:
                return False
        elif single is not None:
            if et != single:
                return False
        else:
            return False

        conditions = trigger.get("conditions")
        if conditions is not None:
            if not isinstance(conditions, dict):
                return False
            for k, v in conditions.items():
                if event.get(k) != v:
                    return False

        return True

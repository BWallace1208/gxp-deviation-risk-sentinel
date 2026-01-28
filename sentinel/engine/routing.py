from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class RoutingDecision:
    consumers: List[str]


class RoutingPolicy:
    def __init__(self, policy_path: Path):
        if not policy_path.exists():
            raise FileNotFoundError(f"Routing policy not found: {policy_path}")
        doc = json.loads(policy_path.read_text(encoding="utf-8"))
        self.version = str(doc.get("version", "unknown"))
        self.allowed = set(str(x) for x in (doc.get("allowed_consumers", []) or []))
        self.aliases: Dict[str, str] = {str(k): str(v) for k, v in (doc.get("aliases", {}) or {}).items()}

        if not self.allowed:
            raise ValueError("Routing policy allowed_consumers is empty; refusing to run.")

    def normalize(self, consumers: Optional[List[str]]) -> RoutingDecision:
        if not consumers:
            return RoutingDecision(consumers=[])

        normalized: List[str] = []
        for c in consumers:
            c = str(c).strip()
            c = self.aliases.get(c, c)
            normalized.append(c)

        # enforce allow-list
        for c in normalized:
            if c not in self.allowed:
                raise ValueError(f"Routing consumer '{c}' is not in allowed_consumers allow-list.")

        # stable order (deterministic)
        return RoutingDecision(consumers=sorted(set(normalized)))

"""
Offline contradiction checks for stable universal facts.

Coverage is intentionally curated rather than open-ended. The fact catalog is
data-driven so new stable facts can be added without changing scoring code.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

CATALOG_PATH = Path(__file__).with_name("facts_catalog.json")
_CATALOG_CACHE: list["UniversalFactRule"] | None = None


@dataclass(frozen=True)
class UniversalFactRule:
    name: str
    pattern: re.Pattern[str]
    message: str
    expected_group: Optional[int] = None
    expected_value: Optional[str] = None


def _load_catalog() -> list[UniversalFactRule]:
    global _CATALOG_CACHE
    if _CATALOG_CACHE is not None:
        return _CATALOG_CACHE

    raw_rules = json.loads(CATALOG_PATH.read_text())
    _CATALOG_CACHE = [
        UniversalFactRule(
            name=item["name"],
            pattern=re.compile(item["pattern"]),
            message=item["message"],
            expected_group=item.get("expected_group"),
            expected_value=item.get("expected_value"),
        )
        for item in raw_rules
    ]
    return _CATALOG_CACHE


def _match_rule(text: str, rule: UniversalFactRule) -> str | None:
    match = rule.pattern.search(text)
    if not match:
        return None

    if rule.expected_group is None:
        return rule.message

    actual_value = match.group(rule.expected_group)
    if actual_value != rule.expected_value:
        return rule.message
    return None


def _matches_verified_fact(text: str, rule: UniversalFactRule) -> bool:
    match = rule.pattern.search(text)
    if not match:
        return False
    if rule.expected_group is None:
        return False
    return match.group(rule.expected_group) == rule.expected_value


def detect_universal_fact_contradictions(text: str) -> List[str]:
    normalized = (text or "").lower()
    findings: List[str] = []

    for rule in _load_catalog():
        hit = _match_rule(normalized, rule)
        if hit:
            findings.append(hit)

    return list(dict.fromkeys(findings))


def detect_verified_universal_facts(text: str) -> List[str]:
    normalized = (text or "").lower()
    matches: List[str] = []

    for rule in _load_catalog():
        if _matches_verified_fact(normalized, rule):
            matches.append(rule.name)

    return list(dict.fromkeys(matches))

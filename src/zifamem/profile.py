"""User profile consolidation from long-term memories."""

from __future__ import annotations

import re
from typing import Any

from zifamem.schemas import MemoryCategory, MemoryRecord, UserProfile, utcnow

IDENTITY_FIELDS = {
    "name",
    "age",
    "occupation",
    "city",
    "identity",
}
PREFERENCE_FIELDS = {"likes", "dislikes"}
RELATIONSHIP_FIELDS = {
    "boundaries",
    "conflicts",
    "vulnerable_topics",
    "memorable_moments",
}
GUARDED_IDENTITY_FIELDS = {"name", "age", "occupation", "city"}


def apply_memory_to_profile(profile: UserProfile, memory: MemoryRecord) -> bool:
    """Merge one memory into an L4 user profile with conservative guards."""

    changed = False
    if memory.category is MemoryCategory.USER_IDENTITY:
        changed = _merge_identity(profile, memory) or changed
    elif memory.category is MemoryCategory.PREFERENCE:
        changed = _merge_preferences(profile, memory) or changed
    elif memory.category is MemoryCategory.BOUNDARY:
        changed = _append_relationship(profile, "boundaries", memory.text) or changed
    elif memory.emotion.conflict:
        changed = _append_relationship(profile, "conflicts", memory.text) or changed
    elif memory.emotion.vulnerability:
        changed = _append_relationship(profile, "vulnerable_topics", memory.text) or changed
    elif memory.category in {
        MemoryCategory.LIFE_EVENT,
        MemoryCategory.MILESTONE,
        MemoryCategory.SHARED_EXPERIENCE,
    }:
        changed = _append_relationship(profile, "memorable_moments", memory.text) or changed

    if changed:
        profile.evidence_count += 1
        profile.version += 1
        profile.last_updated = utcnow()
    return changed


def _merge_identity(profile: UserProfile, memory: MemoryRecord) -> bool:
    updates: dict[str, Any] = {}
    text = memory.text
    patterns = [
        (r"User name is ([^.;\n]+)", "name"),
        (r"User age is ([0-9]{1,3})", "age"),
        (r"User works as ([^.;\n]+)", "occupation"),
        (r"User lives in ([^.;\n]+)", "city"),
        (r"User identity: ([^.;\n]+)", "identity"),
    ]
    for pattern, field in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            updates[field] = _clean_value(match.group(1))

    return _safe_merge(profile.identity, updates, profile.evidence_count)


def _merge_preferences(profile: UserProfile, memory: MemoryRecord) -> bool:
    text = memory.text
    changed = False
    like = re.search(r"User likes ([^.;\n]+)", text, re.IGNORECASE)
    dislike = re.search(r"User dislikes ([^.;\n]+)", text, re.IGNORECASE)
    if like:
        changed = _append_unique(profile.preferences, "likes", _clean_value(like.group(1))) or changed
    if dislike:
        changed = _append_unique(profile.preferences, "dislikes", _clean_value(dislike.group(1))) or changed
    return changed


def _safe_merge(target: dict[str, Any], updates: dict[str, Any], evidence_count: int) -> bool:
    changed = False
    for key, value in updates.items():
        if key not in IDENTITY_FIELDS:
            continue
        if not _valid_value(value):
            continue
        existing = target.get(key)
        if existing in (None, ""):
            target[key] = value
            changed = True
            continue
        if key in GUARDED_IDENTITY_FIELDS and str(existing).lower() != str(value).lower():
            if evidence_count < 3:
                continue
        if str(existing) != str(value):
            target[key] = value
            changed = True
    return changed


def _append_relationship(profile: UserProfile, key: str, value: str) -> bool:
    if key not in RELATIONSHIP_FIELDS:
        return False
    return _append_unique(profile.relationship, key, value[:180])


def _append_unique(target: dict[str, Any], key: str, value: str) -> bool:
    if not _valid_value(value):
        return False
    items = target.get(key)
    if not isinstance(items, list):
        items = []
    if any(str(item).lower() == value.lower() for item in items):
        return False
    if len(items) >= 20:
        return False
    items.append(value)
    target[key] = items
    return True


def _valid_value(value: Any) -> bool:
    if value in (None, "", [], {}):
        return False
    return len(str(value)) <= 200


def _clean_value(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())[:200].strip(" ,.;:!?")

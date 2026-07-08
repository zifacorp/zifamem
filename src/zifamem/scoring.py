"""Memory lifecycle and retrieval scoring."""

from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Iterable

from zifamem.schemas import MemoryRecord, clamp

DECAY_THRESHOLD = 0.1
IMPORTANCE_FLOOR = 0.1


def compute_strength(
    importance: float,
    emotion_intensity: float,
    access_count: int,
    age_days: float,
    pinned: bool = False,
    base_half_life_days: float = 7.0,
) -> float:
    """Compute memory strength with time decay and reinforcement."""

    if pinned:
        return clamp(importance)

    importance = max(IMPORTANCE_FLOOR, clamp(importance))
    emotion_intensity = clamp(emotion_intensity)
    access_count = max(0, int(access_count))
    age_days = max(0.0, float(age_days))
    base_half_life_days = base_half_life_days if base_half_life_days > 0 else 7.0

    if emotion_intensity >= 0.7:
        emotion_factor = 2.0
    elif emotion_intensity >= 0.4:
        emotion_factor = 1.5
    else:
        emotion_factor = 1.0

    reinforcement = min(1.0 + math.log1p(access_count), 3.0)
    half_life = base_half_life_days * emotion_factor * reinforcement
    return clamp(importance * math.pow(0.5, age_days / half_life))


def is_decayed(strength: float, threshold: float = DECAY_THRESHOLD) -> bool:
    return float(strength) <= threshold


def rank_memories(
    memories: Iterable[MemoryRecord],
    query: str,
    *,
    now: datetime | None = None,
    top_k: int = 5,
    semantic_weight: float = 0.35,
    strength_weight: float = 0.30,
    importance_weight: float = 0.25,
    emotion_weight: float = 0.10,
) -> list[MemoryRecord]:
    """Return top memories by semantic fit, strength, importance, and emotion."""

    scored: list[tuple[float, MemoryRecord]] = []
    for memory in memories:
        if memory.is_deleted:
            continue
        strength = compute_strength(
            memory.importance,
            memory.emotion.intensity,
            memory.access_count,
            memory.age_days(now),
            memory.pinned,
        )
        memory.strength = strength
        semantic = text_similarity(query, memory.text)
        emotion = memory.emotion.intensity
        score = (
            semantic_weight * semantic
            + strength_weight * strength
            + importance_weight * memory.importance
            + emotion_weight * emotion
        )
        scored.append((score, memory))

    scored.sort(key=lambda item: item[0], reverse=True)
    results = [memory for _, memory in scored[:top_k]]
    for memory in results:
        memory.touch(now)
    return results


def text_similarity(left: str, right: str) -> float:
    """Small dependency-free lexical similarity for the default store."""

    left_tokens = set(tokenize(left))
    right_tokens = set(tokenize(right))
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    return overlap / union if union else 0.0


def tokenize(text: str) -> list[str]:
    return re.findall(r"[\w']+|[\u4e00-\u9fff]", text.lower())

"""Memory extraction interfaces and default heuristic extractor."""

from __future__ import annotations

import re
from collections import Counter
from typing import Protocol

from zifamem.schemas import (
    ConversationTurn,
    EmotionSignal,
    MemoryCategory,
    MemoryRecord,
    SessionSummary,
)
from zifamem.scoring import tokenize


class MemoryExtractor(Protocol):
    """Interface for extracting memory signals from a completed session."""

    def summarize_session(
        self,
        *,
        session_id: str,
        user_id: str,
        agent_id: str,
        turns: list[ConversationTurn],
    ) -> SessionSummary:
        ...

    def memories_from_summary(self, summary: SessionSummary) -> list[MemoryRecord]:
        ...


class HeuristicMemoryExtractor:
    """A no-dependency extractor for demos, tests, and fallback operation."""

    def summarize_session(
        self,
        *,
        session_id: str,
        user_id: str,
        agent_id: str,
        turns: list[ConversationTurn],
    ) -> SessionSummary:
        eligible_user_texts = [turn.text.strip() for turn in turns if turn.is_memory_eligible]
        summary_text = _summary_from_texts(eligible_user_texts)
        facts = _extract_user_facts(eligible_user_texts)
        emotion = _detect_emotion(" ".join(eligible_user_texts))
        category = _infer_category(facts or eligible_user_texts)
        key_topics = _key_topics(eligible_user_texts)
        importance = _importance_score(facts, emotion, category)

        return SessionSummary(
            session_id=session_id,
            user_id=user_id,
            agent_id=agent_id,
            summary=summary_text,
            key_topics=key_topics,
            emotion_trend=emotion.mood,
            importance_score=importance,
            had_emotional_peak=emotion.intensity >= 0.7,
            user_facts=facts,
            memory_category=category,
            turn_count=len([turn for turn in turns if turn.text.strip()]),
        )

    def memories_from_summary(self, summary: SessionSummary) -> list[MemoryRecord]:
        memories: list[MemoryRecord] = []
        emotion = _detect_emotion(" ".join(summary.user_facts + [summary.summary]))
        for fact in summary.user_facts:
            memory = MemoryRecord(
                user_id=summary.user_id,
                agent_id=summary.agent_id,
                text=fact,
                category=_infer_category([fact]) or summary.memory_category,
                importance=summary.importance_score,
                emotion=emotion,
                strength=summary.importance_score,
                source_session_id=summary.session_id,
                evidence=[summary.session_id],
            )
            memories.append(memory)
        return memories


def _summary_from_texts(texts: list[str]) -> str:
    if not texts:
        return "No memory-eligible user content."
    if len(texts) <= 3:
        return "; ".join(texts)[:280]
    return "; ".join(texts[:2] + ["..."] + texts[-2:])[:320]


def _extract_user_facts(texts: list[str]) -> list[str]:
    facts: list[str] = []
    for text in texts:
        facts.extend(_extract_identity_facts(text))
        facts.extend(_extract_preference_facts(text))
        facts.extend(_extract_life_event_facts(text))
        facts.extend(_extract_boundary_facts(text))
    return _dedupe_preserve_order(facts)


def _extract_identity_facts(text: str) -> list[str]:
    facts: list[str] = []
    patterns = [
        (r"\bmy name is ([A-Za-z][A-Za-z .'-]{0,80}?)(?:\s+and\b|[.;,!?\n]|$)", "User name is {value}"),
        (r"\bi am ([0-9]{1,3}) years old\b", "User age is {value}"),
        (r"\bi work as (?:a |an )?([^.;,!?\n]{2,80}?)(?:\s+and\b|[.;,!?\n]|$)", "User works as {value}"),
        (r"\bi live in ([^.;,!?\n]{2,80}?)(?:\s+and\b|[.;,!?\n]|$)", "User lives in {value}"),
        (r"我叫([^，。,.!\n]{1,30})", "User name is {value}"),
        (r"我住在([^，。,.!\n]{1,40})", "User lives in {value}"),
        (r"我是([^，。,.!\n]{1,40})", "User identity: {value}"),
    ]
    for pattern, template in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = match.group(1).strip()
            if value:
                facts.append(template.format(value=value))
    return facts


def _extract_preference_facts(text: str) -> list[str]:
    facts: list[str] = []
    patterns = [
        (r"\bi (?:really )?(?:like|love|enjoy) ([^.;!?\n]{2,120})", "User likes {value}"),
        (r"\bi (?:do not|don't|hate|dislike) ([^.;!?\n]{2,120})", "User dislikes {value}"),
        (r"我(?:很)?喜欢([^，。,.!\n]{1,80})", "User likes {value}"),
        (r"我(?:不喜欢|讨厌)([^，。,.!\n]{1,80})", "User dislikes {value}"),
    ]
    for pattern, template in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = _clean_fact_value(match.group(1))
            if value:
                facts.append(template.format(value=value))
    return facts


def _extract_life_event_facts(text: str) -> list[str]:
    facts: list[str] = []
    event_keywords = (
        "interview",
        "moved",
        "moving",
        "graduated",
        "married",
        "breakup",
        "surgery",
        "exam",
        "promotion",
        "started a new job",
        "面试",
        "搬家",
        "毕业",
        "结婚",
        "分手",
        "生病",
        "手术",
        "考试",
        "入职",
        "离职",
        "升职",
    )
    lowered = text.lower()
    if any(keyword in lowered for keyword in event_keywords):
        facts.append("User life event: " + text.strip()[:180])
    return facts


def _extract_boundary_facts(text: str) -> list[str]:
    lowered = text.lower()
    boundary_markers = (
        "do not call me",
        "don't call me",
        "please stop",
        "i am not comfortable",
        "不要叫我",
        "别叫我",
        "不要再",
        "不舒服",
        "边界",
    )
    if any(marker in lowered for marker in boundary_markers):
        return ["User boundary: " + text.strip()[:180]]
    return []


def _detect_emotion(text: str) -> EmotionSignal:
    lowered = text.lower()
    positive = ("happy", "excited", "grateful", "love", "relieved", "开心", "高兴", "感谢", "喜欢")
    negative = ("sad", "angry", "anxious", "afraid", "hurt", "lonely", "难过", "生气", "焦虑", "害怕", "委屈")
    conflict = ("fight", "argue", "upset with you", "conflict", "吵架", "冲突", "生你的气")
    vulnerable = ("i feel", "i felt", "i am scared", "i'm scared", "我觉得", "我害怕", "我很难过")
    boundary = ("do not", "don't", "please stop", "不要", "别", "不舒服")

    pos_hits = sum(1 for marker in positive if marker in lowered)
    neg_hits = sum(1 for marker in negative if marker in lowered)
    valence = 0.0
    if pos_hits or neg_hits:
        valence = max(-1.0, min(1.0, (pos_hits - neg_hits) / max(pos_hits + neg_hits, 1)))
    intensity = min(1.0, 0.25 + 0.2 * (pos_hits + neg_hits))
    conflict_hit = any(marker in lowered for marker in conflict)
    vulnerability_hit = any(marker in lowered for marker in vulnerable)
    boundary_hit = any(marker in lowered for marker in boundary)
    if conflict_hit or vulnerability_hit or boundary_hit:
        intensity = max(intensity, 0.65)

    if conflict_hit:
        mood = "conflict"
    elif boundary_hit:
        mood = "boundary"
    elif valence > 0:
        mood = "positive"
    elif valence < 0:
        mood = "negative"
    else:
        mood = "neutral"

    return EmotionSignal(
        mood=mood,
        valence=valence,
        arousal=intensity,
        intensity=intensity,
        trust_delta=-0.2 if conflict_hit else 0.0,
        comfort_delta=-0.2 if boundary_hit else 0.0,
        conflict=conflict_hit,
        vulnerability=vulnerability_hit,
        attachment=("miss you" in lowered or "想你" in lowered),
        boundary=boundary_hit,
    )


def _infer_category(values: list[str]) -> MemoryCategory:
    combined = " ".join(values).lower()
    if "boundary" in combined or "边界" in combined or "不要" in combined:
        return MemoryCategory.BOUNDARY
    if "name is" in combined or "age is" in combined or "works as" in combined or "identity:" in combined:
        return MemoryCategory.USER_IDENTITY
    if "likes" in combined or "dislikes" in combined or "喜欢" in combined or "讨厌" in combined:
        return MemoryCategory.PREFERENCE
    if "life event" in combined:
        return MemoryCategory.LIFE_EVENT
    if "promise" in combined or "答应" in combined:
        return MemoryCategory.PROMISE
    return MemoryCategory.SHARED_EXPERIENCE


def _importance_score(
    facts: list[str],
    emotion: EmotionSignal,
    category: MemoryCategory,
) -> float:
    score = 0.3
    if facts:
        score += 0.2
    if category in {
        MemoryCategory.USER_IDENTITY,
        MemoryCategory.BOUNDARY,
        MemoryCategory.LIFE_EVENT,
        MemoryCategory.PROMISE,
        MemoryCategory.MILESTONE,
    }:
        score += 0.2
    score += min(0.25, emotion.intensity * 0.25)
    return max(0.0, min(1.0, score))


def _key_topics(texts: list[str], limit: int = 5) -> list[str]:
    tokens = [
        token
        for text in texts
        for token in tokenize(text)
        if len(token) > 2 and token not in {"the", "and", "you", "that", "this", "with"}
    ]
    return [token for token, _ in Counter(tokens).most_common(limit)]


def _clean_fact_value(value: str) -> str:
    value = value.strip()
    value = re.sub(r"\s+", " ", value)
    return value[:120].strip(" ,.;:!?")


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item.strip())
    return result

"""LLM-backed memory extraction adapters."""

from __future__ import annotations

from typing import Any

from zifamem.extractors import HeuristicMemoryExtractor, MemoryExtractor
from zifamem.llm import LLMProvider
from zifamem.schemas import (
    ConversationTurn,
    EmotionSignal,
    MemoryCategory,
    MemoryRecord,
    SessionSummary,
    clamp,
)
from zifamem.scoring import tokenize

PSEUDO_TURN_KINDS = {"event_hint", "system_prompt", "tool_trace"}
FACT_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "before",
    "fact",
    "facts",
    "for",
    "is",
    "likes",
    "dislikes",
    "name",
    "the",
    "to",
    "user",
    "with",
}


class LLMMemoryExtractor:
    """MemoryExtractor implementation that delegates extraction to an LLMProvider."""

    def __init__(
        self,
        provider: LLMProvider,
        *,
        fallback: MemoryExtractor | None = None,
        max_prompt_chars: int = 8000,
    ) -> None:
        self.provider = provider
        self.fallback = fallback or HeuristicMemoryExtractor()
        self.max_prompt_chars = max_prompt_chars

    def summarize_session(
        self,
        *,
        session_id: str,
        user_id: str,
        agent_id: str,
        turns: list[ConversationTurn],
    ) -> SessionSummary:
        fallback = self.fallback.summarize_session(
            session_id=session_id,
            user_id=user_id,
            agent_id=agent_id,
            turns=turns,
        )
        eligible_user_texts = [turn.text.strip() for turn in turns if turn.is_memory_eligible]
        if not eligible_user_texts:
            return fallback

        prompt = _summarize_prompt(turns, self.max_prompt_chars)
        data = _safe_generate_json(
            self.provider,
            system=_summary_system_prompt(),
            user=prompt,
        )
        if data is None:
            return fallback

        return _coerce_summary(
            data,
            fallback=fallback,
            session_id=session_id,
            user_id=user_id,
            agent_id=agent_id,
            turns=turns,
            eligible_user_texts=eligible_user_texts,
        )

    def memories_from_summary(self, summary: SessionSummary) -> list[MemoryRecord]:
        fallback = self.fallback.memories_from_summary(summary)
        if not summary.user_facts:
            return fallback

        data = _safe_generate_json(
            self.provider,
            system=_memory_system_prompt(),
            user=_memory_prompt(summary),
        )
        if data is None:
            return fallback

        memories = _coerce_memories(data, summary)
        return memories or fallback


def _safe_generate_json(provider: LLMProvider, *, system: str, user: str) -> dict[str, Any] | None:
    try:
        data = provider.generate_json(system=system, user=user)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _summary_system_prompt() -> str:
    categories = ", ".join(category.value for category in MemoryCategory)
    return (
        "You extract ZifaMem session summaries for an AI companion memory system. "
        "Return one JSON object only. Save only user-grounded facts from user turns. "
        "Assistant, system, event, and tool messages are context only and must never "
        "become user facts. Use these memory_category values: "
        f"{categories}. The JSON shape is: "
        '{"summary": str, "user_facts": [str], "key_topics": [str], '
        '"emotion_trend": str, "importance_score": number, '
        '"had_emotional_peak": boolean, "memory_category": str}.'
    )


def _memory_system_prompt() -> str:
    categories = ", ".join(category.value for category in MemoryCategory)
    return (
        "Convert validated ZifaMem user facts into long-term memory records. "
        "Return one JSON object only. Each memory must be supported by a supplied "
        "user fact. Use these category values: "
        f"{categories}. The JSON shape is: "
        '{"memories": [{"text": str, "category": str, "importance": number, '
        '"emotion": {"mood": str, "valence": number, "arousal": number, '
        '"intensity": number, "trust_delta": number, "comfort_delta": number, '
        '"conflict": boolean, "vulnerability": boolean, "attachment": boolean, '
        '"boundary": boolean}}]}.'
    )


def _summarize_prompt(turns: list[ConversationTurn], max_chars: int) -> str:
    lines: list[str] = []
    for turn in turns:
        if not _is_prompt_turn(turn):
            continue
        label = "User" if turn.is_user else "Agent"
        lines.append(f"{label}: {_clean_text(turn.text, 1000)}")

    rendered = "\n".join(lines)
    if len(rendered) > max_chars:
        rendered = rendered[-max_chars:]
    return "Conversation:\n" + rendered


def _memory_prompt(summary: SessionSummary) -> str:
    facts = "\n".join(f"- {fact}" for fact in summary.user_facts)
    return (
        f"Session summary: {summary.summary}\n"
        f"Emotion trend: {summary.emotion_trend or 'neutral'}\n"
        f"Default category: {summary.memory_category.value}\n"
        f"Default importance: {summary.importance_score}\n"
        f"Validated user facts:\n{facts}"
    )


def _is_prompt_turn(turn: ConversationTurn) -> bool:
    if turn.metadata.get("kind") in PSEUDO_TURN_KINDS:
        return False
    if turn.is_user:
        return turn.is_memory_eligible
    return turn.speaker.lower() in {"agent", "assistant"} and bool(turn.text.strip())


def _coerce_summary(
    data: dict[str, Any],
    *,
    fallback: SessionSummary,
    session_id: str,
    user_id: str,
    agent_id: str,
    turns: list[ConversationTurn],
    eligible_user_texts: list[str],
) -> SessionSummary:
    raw_facts = _string_list(data.get("user_facts"), max_items=12, max_len=240)
    user_facts = [
        fact for fact in raw_facts if _has_user_evidence(fact, eligible_user_texts)
    ]
    user_facts = _dedupe_preserve_order(user_facts)

    return SessionSummary(
        session_id=session_id,
        user_id=user_id,
        agent_id=agent_id,
        summary=_clean_text(data.get("summary"), 700) or fallback.summary,
        key_topics=_string_list(data.get("key_topics"), max_items=8, max_len=40)
        or fallback.key_topics,
        emotion_trend=_clean_text(data.get("emotion_trend"), 40) or fallback.emotion_trend,
        importance_score=_coerce_float(data.get("importance_score"), fallback.importance_score),
        had_emotional_peak=_coerce_bool(data.get("had_emotional_peak"), fallback.had_emotional_peak),
        user_facts=user_facts,
        memory_category=_coerce_category(data.get("memory_category"), fallback.memory_category),
        turn_count=len([turn for turn in turns if turn.text.strip()]),
    )


def _coerce_memories(data: dict[str, Any], summary: SessionSummary) -> list[MemoryRecord]:
    raw_memories = data.get("memories")
    if not isinstance(raw_memories, list):
        return []

    memories: list[MemoryRecord] = []
    for raw in raw_memories[:12]:
        if not isinstance(raw, dict):
            continue
        text = _clean_text(raw.get("text") or raw.get("fact"), 240)
        if not text or not _has_user_evidence(text, summary.user_facts):
            continue
        importance = _coerce_float(raw.get("importance"), summary.importance_score)
        memory = MemoryRecord(
            user_id=summary.user_id,
            agent_id=summary.agent_id,
            text=text,
            category=_coerce_category(raw.get("category"), summary.memory_category),
            importance=importance,
            emotion=_coerce_emotion(raw.get("emotion"), summary.emotion_trend),
            strength=importance,
            source_session_id=summary.session_id,
            evidence=[summary.session_id],
            metadata={"extractor": "llm"},
        )
        memories.append(memory)
    return memories


def _coerce_emotion(raw: Any, fallback_mood: str | None) -> EmotionSignal:
    if isinstance(raw, dict):
        try:
            return EmotionSignal.from_dict(raw)
        except (TypeError, ValueError):
            pass
    return EmotionSignal(mood=fallback_mood or "neutral").normalized()


def _coerce_category(raw: Any, fallback: MemoryCategory) -> MemoryCategory:
    try:
        return MemoryCategory(str(raw))
    except (TypeError, ValueError):
        return fallback


def _coerce_float(raw: Any, fallback: float) -> float:
    try:
        return clamp(float(raw))
    except (TypeError, ValueError):
        return clamp(fallback)


def _coerce_bool(raw: Any, fallback: bool) -> bool:
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        lowered = raw.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return bool(fallback)


def _string_list(raw: Any, *, max_items: int, max_len: int) -> list[str]:
    if isinstance(raw, str):
        raw_items: list[Any] = [raw]
    elif isinstance(raw, list):
        raw_items = raw
    else:
        return []

    items: list[str] = []
    for item in raw_items:
        text = _clean_text(item, max_len)
        if text:
            items.append(text)
        if len(items) >= max_items:
            break
    return _dedupe_preserve_order(items)


def _clean_text(raw: Any, max_len: int) -> str:
    if raw is None:
        return ""
    text = " ".join(str(raw).strip().split())
    return text[:max_len].strip()


def _has_user_evidence(fact: str, eligible_user_texts: list[str]) -> bool:
    if not eligible_user_texts:
        return False
    user_text = " ".join(eligible_user_texts).lower()
    fact_text = fact.lower()
    user_tokens = set(tokenize(user_text))
    fact_tokens = [
        token
        for token in tokenize(fact_text)
        if (len(token) > 2 or token.isdigit()) and token not in FACT_STOPWORDS
    ]
    if not fact_tokens:
        return True
    for token in fact_tokens:
        if token in user_tokens or token in user_text:
            return True
    return any(_cjk_substring in user_text for _cjk_substring in _cjk_substrings(fact_text))


def _cjk_substrings(text: str) -> list[str]:
    cjk_chars = [char for char in text if "\u4e00" <= char <= "\u9fff"]
    if len(cjk_chars) < 2:
        return []
    joined = "".join(cjk_chars)
    return [joined[index : index + 2] for index in range(len(joined) - 1)]


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

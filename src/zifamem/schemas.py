"""Core ZifaMem data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, float(value)))


class MemoryCategory(str, Enum):
    USER_IDENTITY = "user_identity"
    PREFERENCE = "preference"
    LIFE_EVENT = "life_event"
    SHARED_EXPERIENCE = "shared_experience"
    PROMISE = "promise"
    MILESTONE = "milestone"
    BOUNDARY = "boundary"
    REPAIR = "repair"
    EMOTIONAL_PATTERN = "emotional_pattern"


@dataclass(slots=True)
class EmotionSignal:
    """Emotion and relationship signal attached to a memory."""

    mood: str = "neutral"
    valence: float = 0.0
    arousal: float = 0.0
    intensity: float = 0.0
    trust_delta: float = 0.0
    comfort_delta: float = 0.0
    conflict: bool = False
    vulnerability: bool = False
    attachment: bool = False
    boundary: bool = False

    def normalized(self) -> "EmotionSignal":
        return EmotionSignal(
            mood=self.mood or "neutral",
            valence=max(-1.0, min(1.0, float(self.valence))),
            arousal=clamp(self.arousal),
            intensity=clamp(self.intensity),
            trust_delta=max(-1.0, min(1.0, float(self.trust_delta))),
            comfort_delta=max(-1.0, min(1.0, float(self.comfort_delta))),
            conflict=bool(self.conflict),
            vulnerability=bool(self.vulnerability),
            attachment=bool(self.attachment),
            boundary=bool(self.boundary),
        )

    def to_dict(self) -> dict[str, Any]:
        normalized = self.normalized()
        return {
            "mood": normalized.mood,
            "valence": normalized.valence,
            "arousal": normalized.arousal,
            "intensity": normalized.intensity,
            "trust_delta": normalized.trust_delta,
            "comfort_delta": normalized.comfort_delta,
            "conflict": normalized.conflict,
            "vulnerability": normalized.vulnerability,
            "attachment": normalized.attachment,
            "boundary": normalized.boundary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "EmotionSignal":
        if not data:
            return cls()
        return cls(
            mood=str(data.get("mood", "neutral")),
            valence=float(data.get("valence", 0.0)),
            arousal=float(data.get("arousal", 0.0)),
            intensity=float(data.get("intensity", 0.0)),
            trust_delta=float(data.get("trust_delta", 0.0)),
            comfort_delta=float(data.get("comfort_delta", 0.0)),
            conflict=bool(data.get("conflict", False)),
            vulnerability=bool(data.get("vulnerability", False)),
            attachment=bool(data.get("attachment", False)),
            boundary=bool(data.get("boundary", False)),
        ).normalized()


@dataclass(slots=True)
class ConversationTurn:
    """One observed dialogue turn."""

    speaker: str
    text: str
    session_id: str
    user_id: str
    agent_id: str
    created_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_user(self) -> bool:
        return self.speaker.lower() in {"user", "human"}

    @property
    def is_memory_eligible(self) -> bool:
        if not self.is_user:
            return False
        if self.metadata.get("memory_eligible") is False:
            return False
        if self.metadata.get("kind") in {"event_hint", "system_prompt", "tool_trace"}:
            return False
        return bool(self.text.strip())

    def to_prompt_line(self) -> str:
        label = "User" if self.is_user else "Agent"
        return f"{label}: {self.text.strip()}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "speaker": self.speaker,
            "text": self.text,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationTurn":
        created = data.get("created_at")
        return cls(
            speaker=str(data["speaker"]),
            text=str(data["text"]),
            session_id=str(data["session_id"]),
            user_id=str(data["user_id"]),
            agent_id=str(data["agent_id"]),
            created_at=datetime.fromisoformat(created) if created else utcnow(),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass(slots=True)
class SessionSummary:
    """L2 summary produced when a session boundary is reached."""

    session_id: str
    user_id: str
    agent_id: str
    summary: str
    key_topics: list[str] = field(default_factory=list)
    emotion_trend: str | None = None
    importance_score: float = 0.3
    had_emotional_peak: bool = False
    user_facts: list[str] = field(default_factory=list)
    memory_category: MemoryCategory = MemoryCategory.SHARED_EXPERIENCE
    turn_count: int = 0
    created_at: datetime = field(default_factory=utcnow)

    def to_prompt_text(self) -> str:
        date_label = self.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d")
        topics = ", ".join(self.key_topics) if self.key_topics else "none"
        text = f"[{date_label} session, {self.turn_count} turns] {self.summary}\nTopics: {topics}"
        if self.user_facts:
            text += "\nUser facts: " + "; ".join(self.user_facts)
        return text

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "summary": self.summary,
            "key_topics": self.key_topics,
            "emotion_trend": self.emotion_trend,
            "importance_score": clamp(self.importance_score),
            "had_emotional_peak": self.had_emotional_peak,
            "user_facts": self.user_facts,
            "memory_category": self.memory_category.value,
            "turn_count": self.turn_count,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionSummary":
        created = data.get("created_at")
        return cls(
            session_id=str(data["session_id"]),
            user_id=str(data["user_id"]),
            agent_id=str(data["agent_id"]),
            summary=str(data.get("summary", "")),
            key_topics=list(data.get("key_topics") or []),
            emotion_trend=data.get("emotion_trend"),
            importance_score=float(data.get("importance_score", 0.3)),
            had_emotional_peak=bool(data.get("had_emotional_peak", False)),
            user_facts=list(data.get("user_facts") or []),
            memory_category=MemoryCategory(data.get("memory_category", "shared_experience")),
            turn_count=int(data.get("turn_count", 0)),
            created_at=datetime.fromisoformat(created) if created else utcnow(),
        )


@dataclass(slots=True)
class MemoryRecord:
    """L3 emotional long-term memory."""

    user_id: str
    agent_id: str
    text: str
    category: MemoryCategory = MemoryCategory.SHARED_EXPERIENCE
    importance: float = 0.5
    emotion: EmotionSignal = field(default_factory=EmotionSignal)
    strength: float = 0.5
    memory_id: str = field(default_factory=lambda: uuid4().hex)
    source_session_id: str | None = None
    evidence: list[str] = field(default_factory=list)
    pinned: bool = False
    access_count: int = 0
    created_at: datetime = field(default_factory=utcnow)
    last_accessed: datetime = field(default_factory=utcnow)
    is_deleted: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.importance = clamp(self.importance)
        self.strength = clamp(self.strength)
        self.emotion = self.emotion.normalized()

    def age_days(self, now: datetime | None = None) -> float:
        current = now or utcnow()
        created = self.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return max(0.0, (current - created).total_seconds() / 86400.0)

    def prompt_label(self, now: datetime | None = None) -> str:
        days = int(self.age_days(now))
        age = "today" if days == 0 else f"{days}d ago"
        level = "important" if self.importance >= 0.6 else "ordinary"
        return f"{age} | {level} | {self.category.value}"

    def touch(self, now: datetime | None = None) -> None:
        self.access_count += 1
        self.last_accessed = now or utcnow()

    def reinforce(self, amount: float = 0.1) -> None:
        self.importance = clamp(self.importance + amount)
        self.strength = clamp(self.strength + amount)

    def weaken(self, amount: float = 0.1) -> None:
        self.strength = clamp(self.strength - amount)

    def forget(self) -> None:
        self.is_deleted = True
        self.strength = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "text": self.text,
            "category": self.category.value,
            "importance": self.importance,
            "emotion": self.emotion.to_dict(),
            "strength": self.strength,
            "source_session_id": self.source_session_id,
            "evidence": self.evidence,
            "pinned": self.pinned,
            "access_count": self.access_count,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "is_deleted": self.is_deleted,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryRecord":
        created = data.get("created_at")
        accessed = data.get("last_accessed")
        return cls(
            memory_id=str(data.get("memory_id") or uuid4().hex),
            user_id=str(data["user_id"]),
            agent_id=str(data["agent_id"]),
            text=str(data.get("text", "")),
            category=MemoryCategory(data.get("category", "shared_experience")),
            importance=float(data.get("importance", 0.5)),
            emotion=EmotionSignal.from_dict(data.get("emotion")),
            strength=float(data.get("strength", 0.5)),
            source_session_id=data.get("source_session_id"),
            evidence=list(data.get("evidence") or []),
            pinned=bool(data.get("pinned", False)),
            access_count=int(data.get("access_count", 0)),
            created_at=datetime.fromisoformat(created) if created else utcnow(),
            last_accessed=datetime.fromisoformat(accessed) if accessed else utcnow(),
            is_deleted=bool(data.get("is_deleted", False)),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass(slots=True)
class UserProfile:
    """L4 user cognition profile."""

    user_id: str
    agent_id: str
    identity: dict[str, Any] = field(default_factory=dict)
    preferences: dict[str, Any] = field(default_factory=dict)
    relationship: dict[str, Any] = field(default_factory=dict)
    evidence_count: int = 0
    version: int = 1
    last_updated: datetime = field(default_factory=utcnow)

    def to_prompt_summary(self) -> str:
        sections: list[str] = []
        if self.identity:
            sections.append("Identity: " + _format_mapping(self.identity))
        if self.preferences:
            sections.append("Preferences: " + _format_mapping(self.preferences))
        if self.relationship:
            sections.append("Relationship: " + _format_mapping(self.relationship))
        return "\n".join(section for section in sections if section)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "identity": self.identity,
            "preferences": self.preferences,
            "relationship": self.relationship,
            "evidence_count": self.evidence_count,
            "version": self.version,
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserProfile":
        updated = data.get("last_updated")
        return cls(
            user_id=str(data["user_id"]),
            agent_id=str(data["agent_id"]),
            identity=dict(data.get("identity") or {}),
            preferences=dict(data.get("preferences") or {}),
            relationship=dict(data.get("relationship") or {}),
            evidence_count=int(data.get("evidence_count", 0)),
            version=int(data.get("version", 1)),
            last_updated=datetime.fromisoformat(updated) if updated else utcnow(),
        )


def _format_mapping(data: dict[str, Any]) -> str:
    parts: list[str] = []
    for key, value in data.items():
        if value in (None, "", [], {}):
            continue
        if isinstance(value, list):
            rendered = ", ".join(str(item) for item in value)
        else:
            rendered = str(value)
        parts.append(f"{key}: {rendered}")
    return "; ".join(parts)

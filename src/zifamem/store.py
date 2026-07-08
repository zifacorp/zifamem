"""Storage backends for ZifaMem."""

from __future__ import annotations

import json
from pathlib import Path

from zifamem.schemas import (
    ConversationTurn,
    MemoryRecord,
    SessionSummary,
    UserProfile,
)

PairKey = tuple[str, str]


class InMemoryStore:
    """Dependency-free store suitable for tests, demos, and adapters."""

    def __init__(self) -> None:
        self._turns: dict[PairKey, dict[str, list[ConversationTurn]]] = {}
        self._summaries: dict[PairKey, list[SessionSummary]] = {}
        self._memories: dict[PairKey, list[MemoryRecord]] = {}
        self._profiles: dict[PairKey, UserProfile] = {}

    def append_turn(self, turn: ConversationTurn) -> None:
        sessions = self._turns.setdefault((turn.user_id, turn.agent_id), {})
        sessions.setdefault(turn.session_id, []).append(turn)
        self._after_mutation()

    def list_turns(self, user_id: str, agent_id: str, session_id: str) -> list[ConversationTurn]:
        return list(self._turns.get((user_id, agent_id), {}).get(session_id, ()))

    def recent_turns(
        self,
        user_id: str,
        agent_id: str,
        *,
        session_id: str | None = None,
        limit: int = 12,
    ) -> list[ConversationTurn]:
        sessions = self._turns.get((user_id, agent_id), {})
        if session_id is not None:
            return list(sessions.get(session_id, ())[-limit:])
        all_turns = [turn for turns in sessions.values() for turn in turns]
        all_turns.sort(key=lambda turn: turn.created_at)
        return all_turns[-limit:]

    def save_summary(self, summary: SessionSummary, *, max_summaries: int = 10) -> None:
        pair = (summary.user_id, summary.agent_id)
        items = [item for item in self._summaries.get(pair, []) if item.session_id != summary.session_id]
        items.append(summary)
        items.sort(key=lambda item: item.created_at, reverse=True)
        self._summaries[pair] = items[:max_summaries]
        self._after_mutation()

    def recent_summaries(self, user_id: str, agent_id: str, *, limit: int = 3) -> list[SessionSummary]:
        items = list(self._summaries.get((user_id, agent_id), ()))
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items[:limit]

    def save_memory(self, memory: MemoryRecord) -> MemoryRecord:
        pair = (memory.user_id, memory.agent_id)
        items = self._memories.setdefault(pair, [])
        for existing in items:
            if existing.memory_id == memory.memory_id:
                _copy_memory(memory, existing)
                self._after_mutation()
                return existing
            if (
                memory.source_session_id
                and existing.source_session_id == memory.source_session_id
                and existing.text.strip().lower() == memory.text.strip().lower()
            ):
                existing.reinforce(0.05)
                existing.evidence = sorted(set(existing.evidence + memory.evidence))
                self._after_mutation()
                return existing
        items.append(memory)
        self._after_mutation()
        return memory

    def list_memories(self, user_id: str, agent_id: str, *, include_deleted: bool = False) -> list[MemoryRecord]:
        items = list(self._memories.get((user_id, agent_id), ()))
        if include_deleted:
            return items
        return [item for item in items if not item.is_deleted]

    def get_memory(self, memory_id: str) -> MemoryRecord | None:
        for items in self._memories.values():
            for memory in items:
                if memory.memory_id == memory_id:
                    return memory
        return None

    def delete_memory(self, memory_id: str) -> bool:
        memory = self.get_memory(memory_id)
        if memory is None:
            return False
        memory.forget()
        self._after_mutation()
        return True

    def get_profile(self, user_id: str, agent_id: str) -> UserProfile | None:
        return self._profiles.get((user_id, agent_id))

    def save_profile(self, profile: UserProfile) -> UserProfile:
        self._profiles[(profile.user_id, profile.agent_id)] = profile
        self._after_mutation()
        return profile

    def profile_or_create(self, user_id: str, agent_id: str) -> UserProfile:
        profile = self.get_profile(user_id, agent_id)
        if profile is None:
            profile = UserProfile(user_id=user_id, agent_id=agent_id)
            self.save_profile(profile)
        return profile

    def to_dict(self) -> dict[str, object]:
        return {
            "turns": [
                turn.to_dict()
                for sessions in self._turns.values()
                for turns in sessions.values()
                for turn in turns
            ],
            "summaries": [
                summary.to_dict()
                for summaries in self._summaries.values()
                for summary in summaries
            ],
            "memories": [
                memory.to_dict()
                for memories in self._memories.values()
                for memory in memories
            ],
            "profiles": [profile.to_dict() for profile in self._profiles.values()],
        }

    def load_dict(self, data: dict[str, object]) -> None:
        self._turns.clear()
        self._summaries.clear()
        self._memories.clear()
        self._profiles.clear()
        for raw in data.get("turns", []) or []:
            self.append_turn(ConversationTurn.from_dict(raw))  # type: ignore[arg-type]
        for raw in data.get("summaries", []) or []:
            self.save_summary(SessionSummary.from_dict(raw))  # type: ignore[arg-type]
        for raw in data.get("memories", []) or []:
            self.save_memory(MemoryRecord.from_dict(raw))  # type: ignore[arg-type]
        for raw in data.get("profiles", []) or []:
            self.save_profile(UserProfile.from_dict(raw))  # type: ignore[arg-type]

    def _after_mutation(self) -> None:
        return None


class JsonMemoryStore(InMemoryStore):
    """JSON file store for local development and small deployments."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        super().__init__()
        self._loading = False
        if self.path.exists():
            self._loading = True
            try:
                self.load_dict(json.loads(self.path.read_text(encoding="utf-8")))
            finally:
                self._loading = False

    def _after_mutation(self) -> None:
        if getattr(self, "_loading", False):
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        tmp.replace(self.path)


def _copy_memory(source: MemoryRecord, target: MemoryRecord) -> None:
    target.text = source.text
    target.category = source.category
    target.importance = source.importance
    target.emotion = source.emotion
    target.strength = source.strength
    target.source_session_id = source.source_session_id
    target.evidence = source.evidence
    target.pinned = source.pinned
    target.access_count = source.access_count
    target.created_at = source.created_at
    target.last_accessed = source.last_accessed
    target.is_deleted = source.is_deleted
    target.metadata = source.metadata

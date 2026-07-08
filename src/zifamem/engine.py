"""High-level ZifaMem engine."""

from __future__ import annotations

from zifamem.context import MemoryContext
from zifamem.extractors import HeuristicMemoryExtractor, MemoryExtractor
from zifamem.profile import apply_memory_to_profile
from zifamem.schemas import (
    ConversationTurn,
    EmotionSignal,
    MemoryCategory,
    MemoryRecord,
    SessionSummary,
    UserProfile,
)
from zifamem.scoring import rank_memories
from zifamem.store import InMemoryStore


class ZifaMemory:
    """Orchestrates L1/L2/L3/L4 memory lifecycle for one application."""

    def __init__(
        self,
        *,
        store: InMemoryStore | None = None,
        extractor: MemoryExtractor | None = None,
        l3_importance_threshold: float = 0.5,
    ) -> None:
        self.store = store or InMemoryStore()
        self.extractor = extractor or HeuristicMemoryExtractor()
        self.l3_importance_threshold = l3_importance_threshold

    def record_turn(
        self,
        *,
        user_id: str,
        agent_id: str,
        session_id: str,
        speaker: str,
        text: str,
        metadata: dict | None = None,
    ) -> ConversationTurn:
        """Append a turn to the L1 session buffer."""

        turn = ConversationTurn(
            speaker=speaker,
            text=text,
            session_id=session_id,
            user_id=user_id,
            agent_id=agent_id,
            metadata=metadata or {},
        )
        self.store.append_turn(turn)
        return turn

    def get_context(
        self,
        *,
        user_id: str,
        agent_id: str,
        query: str,
        session_id: str | None = None,
        top_k: int = 5,
        skip_l1: bool = False,
        procedural_rules: tuple[str, ...] = (),
        director_refs: tuple[str, ...] = (),
    ) -> MemoryContext:
        """Read L1/L2/L3/L4 memory into a prompt-ready context."""

        l1_turns: tuple[str, ...] = ()
        if not skip_l1:
            l1_turns = tuple(
                turn.to_prompt_line()
                for turn in self.store.recent_turns(
                    user_id,
                    agent_id,
                    session_id=session_id,
                    limit=12,
                )
            )

        summaries = tuple(
            summary.to_prompt_text()
            for summary in self.store.recent_summaries(user_id, agent_id, limit=3)
        )
        memories = rank_memories(
            self.store.list_memories(user_id, agent_id),
            query,
            top_k=top_k,
        )

        return MemoryContext(
            l1_turns=l1_turns,
            l2_summaries=summaries,
            l3_memories=tuple(memories),
            l4_profile=self.store.get_profile(user_id, agent_id),
            procedural_rules=procedural_rules,
            director_refs=director_refs,
        )

    def end_session(
        self,
        *,
        user_id: str,
        agent_id: str,
        session_id: str,
    ) -> SessionSummary:
        """Run session-boundary consolidation: L1 -> L2 -> optional L3/L4."""

        turns = self.store.list_turns(user_id, agent_id, session_id)
        summary = self.extractor.summarize_session(
            session_id=session_id,
            user_id=user_id,
            agent_id=agent_id,
            turns=turns,
        )
        self.store.save_summary(summary)

        should_upgrade = (
            summary.importance_score >= self.l3_importance_threshold
            or summary.had_emotional_peak
        )
        if should_upgrade:
            for memory in self.extractor.memories_from_summary(summary):
                self.add_memory(memory)
        return summary

    def add_memory(self, memory: MemoryRecord) -> MemoryRecord:
        """Store a L3 memory and update the L4 profile when applicable."""

        saved = self.store.save_memory(memory)
        profile = self.store.profile_or_create(saved.user_id, saved.agent_id)
        apply_memory_to_profile(profile, saved)
        self.store.save_profile(profile)
        return saved

    def remember(
        self,
        *,
        user_id: str,
        agent_id: str,
        text: str,
        category: MemoryCategory = MemoryCategory.SHARED_EXPERIENCE,
        importance: float = 0.5,
        emotion: EmotionSignal | None = None,
        source_session_id: str | None = None,
        pinned: bool = False,
        metadata: dict | None = None,
    ) -> MemoryRecord:
        """Manually create a long-term memory."""

        memory = MemoryRecord(
            user_id=user_id,
            agent_id=agent_id,
            text=text,
            category=category,
            importance=importance,
            emotion=emotion or EmotionSignal(),
            strength=importance,
            source_session_id=source_session_id,
            pinned=pinned,
            metadata=metadata or {},
        )
        return self.add_memory(memory)

    def reinforce(self, memory_id: str, amount: float = 0.1) -> bool:
        memory = self.store.get_memory(memory_id)
        if memory is None:
            return False
        memory.reinforce(amount)
        self.store.save_memory(memory)
        return True

    def weaken(self, memory_id: str, amount: float = 0.1) -> bool:
        memory = self.store.get_memory(memory_id)
        if memory is None:
            return False
        memory.weaken(amount)
        self.store.save_memory(memory)
        return True

    def forget(self, memory_id: str) -> bool:
        memory = self.store.get_memory(memory_id)
        if memory is None:
            return False
        user_id = memory.user_id
        agent_id = memory.agent_id
        deleted = self.store.delete_memory(memory_id)
        if deleted:
            self._rebuild_profile(user_id, agent_id)
        return deleted

    def _rebuild_profile(self, user_id: str, agent_id: str) -> None:
        profile = UserProfile(user_id=user_id, agent_id=agent_id)
        for memory in self.store.list_memories(user_id, agent_id):
            apply_memory_to_profile(profile, memory)
        self.store.save_profile(profile)

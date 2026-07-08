from datetime import timedelta

from zifamem.schemas import EmotionSignal, MemoryRecord, utcnow
from zifamem.scoring import compute_strength, rank_memories


def test_compute_strength_respects_pin_and_decay() -> None:
    pinned = compute_strength(0.7, 0.0, 0, 100, pinned=True)
    old = compute_strength(0.7, 0.0, 0, 100, pinned=False)
    fresh = compute_strength(0.7, 0.0, 0, 0, pinned=False)

    assert pinned == 0.7
    assert old < fresh


def test_rank_memories_balances_semantic_and_emotional_strength() -> None:
    now = utcnow()
    relevant = MemoryRecord(
        user_id="u1",
        agent_id="a1",
        text="User likes quiet check-ins before interviews",
        importance=0.5,
        created_at=now - timedelta(days=2),
    )
    emotional = MemoryRecord(
        user_id="u1",
        agent_id="a1",
        text="User felt anxious before a job interview",
        importance=0.8,
        emotion=EmotionSignal(mood="negative", intensity=0.8),
        created_at=now - timedelta(days=20),
    )

    ranked = rank_memories([emotional, relevant], "interview anxiety", now=now, top_k=2)

    assert ranked[0] is emotional
    assert emotional.access_count == 1

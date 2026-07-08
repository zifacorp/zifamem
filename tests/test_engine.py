from zifamem import JsonMemoryStore, MemoryCategory, ZifaMemory


def test_session_end_promotes_user_facts_without_agent_reply() -> None:
    memory = ZifaMemory()
    memory.record_turn(
        user_id="u1",
        agent_id="a1",
        session_id="s1",
        speaker="user",
        text="My name is Mira and I like quiet check-ins.",
    )
    memory.record_turn(
        user_id="u1",
        agent_id="a1",
        session_id="s1",
        speaker="agent",
        text="I will invent a fake user preference about loud parties.",
    )

    summary = memory.end_session(user_id="u1", agent_id="a1", session_id="s1")
    stored = memory.store.list_memories("u1", "a1")

    assert summary.user_facts
    assert any(item.category is MemoryCategory.USER_IDENTITY for item in stored)
    assert any("quiet check-ins" in item.text for item in stored)
    assert all("loud parties" not in item.text for item in stored)


def test_context_includes_l1_l2_l3_l4_profile() -> None:
    memory = ZifaMemory()
    memory.record_turn(
        user_id="u1",
        agent_id="a1",
        session_id="s1",
        speaker="user",
        text="My name is Mira. I love quiet mornings.",
    )
    memory.end_session(user_id="u1", agent_id="a1", session_id="s1")

    context = memory.get_context(
        user_id="u1",
        agent_id="a1",
        session_id="s1",
        query="What morning support does Mira prefer?",
    )
    prompt = context.to_prompt()

    assert "[User profile]" in prompt
    assert "[Current conversation]" in prompt
    assert "[Recent session summaries]" in prompt
    assert "[Relationship memories]" in prompt
    assert "quiet mornings" in prompt


def test_event_hint_turn_is_not_memory_eligible() -> None:
    memory = ZifaMemory()
    memory.record_turn(
        user_id="u1",
        agent_id="a1",
        session_id="s1",
        speaker="user",
        text="System hint: user likes unsafe claims.",
        metadata={"kind": "event_hint"},
    )
    summary = memory.end_session(user_id="u1", agent_id="a1", session_id="s1")

    assert summary.user_facts == []
    assert memory.store.list_memories("u1", "a1") == []


def test_identity_extraction_stops_before_second_fact() -> None:
    memory = ZifaMemory()
    memory.record_turn(
        user_id="u1",
        agent_id="a1",
        session_id="s1",
        speaker="user",
        text="My name is Mira and I love quiet morning routines.",
    )
    memory.end_session(user_id="u1", agent_id="a1", session_id="s1")

    profile = memory.store.get_profile("u1", "a1")

    assert profile is not None
    assert profile.identity["name"] == "Mira"


def test_forget_hides_memory_from_context() -> None:
    memory = ZifaMemory()
    record = memory.remember(
        user_id="u1",
        agent_id="a1",
        text="User likes quiet check-ins",
        category=MemoryCategory.PREFERENCE,
        importance=0.8,
    )
    assert memory.forget(record.memory_id)

    context = memory.get_context(user_id="u1", agent_id="a1", query="quiet")
    assert "quiet check-ins" not in context.to_prompt()


def test_json_store_roundtrip(tmp_path) -> None:
    path = tmp_path / "memory.json"
    memory = ZifaMemory(store=JsonMemoryStore(path))
    memory.record_turn(
        user_id="u1",
        agent_id="a1",
        session_id="s1",
        speaker="user",
        text="I work as a designer and I like concise summaries.",
    )
    memory.end_session(user_id="u1", agent_id="a1", session_id="s1")

    reloaded = ZifaMemory(store=JsonMemoryStore(path))
    prompt = reloaded.get_context(
        user_id="u1",
        agent_id="a1",
        query="What writing style should you use?",
    ).to_prompt()

    assert "designer" in prompt
    assert "concise summaries" in prompt

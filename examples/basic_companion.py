"""Minimal ZifaMem companion-memory example."""

from zifamem import ZifaMemory


memory = ZifaMemory()

memory.record_turn(
    user_id="u_123",
    agent_id="companion",
    session_id="s_001",
    speaker="user",
    text="My name is Mira and I love quiet morning routines.",
)
memory.record_turn(
    user_id="u_123",
    agent_id="companion",
    session_id="s_001",
    speaker="agent",
    text="Quiet mornings sound grounding.",
)

memory.end_session(user_id="u_123", agent_id="companion", session_id="s_001")

context = memory.get_context(
    user_id="u_123",
    agent_id="companion",
    session_id="s_001",
    query="What should I remember about Mira?",
)

print(context.to_prompt())

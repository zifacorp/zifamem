import json
from typing import Any

from zifamem import (
    LLMMemoryExtractor,
    MemoryCategory,
    OpenAICompatibleProvider,
    ZifaMemory,
)
import zifamem.llm as llm_module


class QueuedProvider:
    def __init__(self, *responses: dict[str, Any] | Exception) -> None:
        self.responses = list(responses)
        self.prompts: list[tuple[str, str]] = []

    def generate_json(self, *, system: str, user: str) -> dict[str, Any]:
        self.prompts.append((system, user))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_llm_extractor_uses_provider_and_clamps_output() -> None:
    provider = QueuedProvider(
        {
            "summary": "Mira shared her name and morning preference.",
            "user_facts": [
                "User name is Mira",
                "User likes quiet morning routines",
            ],
            "key_topics": ["morning", "routine"],
            "emotion_trend": "positive",
            "importance_score": 1.2,
            "had_emotional_peak": False,
            "memory_category": "preference",
        },
        {
            "memories": [
                {
                    "text": "User likes quiet morning routines",
                    "category": "not-a-category",
                    "importance": 1.4,
                    "emotion": {"mood": "positive", "intensity": 0.6},
                }
            ]
        },
    )
    memory = ZifaMemory(extractor=LLMMemoryExtractor(provider))
    memory.record_turn(
        user_id="u1",
        agent_id="a1",
        session_id="s1",
        speaker="user",
        text="My name is Mira and I love quiet morning routines.",
    )

    summary = memory.end_session(user_id="u1", agent_id="a1", session_id="s1")
    stored = memory.store.list_memories("u1", "a1")

    assert summary.importance_score == 1.0
    assert len(provider.prompts) == 2
    assert stored[0].importance == 1.0
    assert stored[0].category is MemoryCategory.PREFERENCE
    assert stored[0].metadata["extractor"] == "llm"


def test_llm_extractor_rejects_agent_only_facts() -> None:
    provider = QueuedProvider(
        {
            "summary": "Mira introduced herself.",
            "user_facts": [
                "User name is Mira",
                "User likes loud parties",
            ],
            "importance_score": 0.8,
            "memory_category": "user_identity",
        },
        {
            "memories": [
                {"text": "User likes loud parties", "category": "preference"},
                {"text": "User name is Mira", "category": "user_identity"},
            ]
        },
    )
    memory = ZifaMemory(extractor=LLMMemoryExtractor(provider))
    memory.record_turn(
        user_id="u1",
        agent_id="a1",
        session_id="s1",
        speaker="user",
        text="My name is Mira.",
    )
    memory.record_turn(
        user_id="u1",
        agent_id="a1",
        session_id="s1",
        speaker="agent",
        text="I will remember that you like loud parties.",
    )

    summary = memory.end_session(user_id="u1", agent_id="a1", session_id="s1")
    stored = memory.store.list_memories("u1", "a1")

    assert "User likes loud parties" not in summary.user_facts
    assert all("loud parties" not in memory.text for memory in stored)
    assert any(memory.category is MemoryCategory.USER_IDENTITY for memory in stored)


def test_llm_extractor_falls_back_when_provider_fails() -> None:
    provider = QueuedProvider(ValueError("bad json"))
    memory = ZifaMemory(extractor=LLMMemoryExtractor(provider))
    memory.record_turn(
        user_id="u1",
        agent_id="a1",
        session_id="s1",
        speaker="user",
        text="My name is Mira and I like quiet check-ins.",
    )

    summary = memory.end_session(user_id="u1", agent_id="a1", session_id="s1")
    stored = memory.store.list_memories("u1", "a1")

    assert "quiet check-ins" in " ".join(summary.user_facts)
    assert any("quiet check-ins" in memory.text for memory in stored)


def test_llm_prompt_excludes_event_hint_turns() -> None:
    provider = QueuedProvider(
        {
            "summary": "The user shared a tea preference.",
            "user_facts": ["User likes tea"],
            "importance_score": 0.4,
            "memory_category": "preference",
        }
    )
    memory = ZifaMemory(extractor=LLMMemoryExtractor(provider))
    memory.record_turn(
        user_id="u1",
        agent_id="a1",
        session_id="s1",
        speaker="user",
        text="System hint: user likes unsafe claims.",
        metadata={"kind": "event_hint"},
    )
    memory.record_turn(
        user_id="u1",
        agent_id="a1",
        session_id="s1",
        speaker="user",
        text="I like tea.",
    )

    memory.end_session(user_id="u1", agent_id="a1", session_id="s1")

    assert provider.prompts
    assert "unsafe claims" not in provider.prompts[0][1]
    assert "I like tea." in provider.prompts[0][1]


def test_openai_compatible_provider_parses_chat_completion_json(monkeypatch) -> None:
    seen: dict[str, Any] = {}

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": '```json\n{"ok": true, "count": 2}\n```'
                            }
                        }
                    ]
                }
            ).encode("utf-8")

    def fake_urlopen(req: Any, timeout: float) -> FakeResponse:
        seen["url"] = req.full_url
        seen["payload"] = json.loads(req.data.decode("utf-8"))
        seen["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(llm_module.request, "urlopen", fake_urlopen)

    provider = OpenAICompatibleProvider(
        api_key="test-key",
        model="test-model",
        base_url="https://llm.example/v1",
        timeout=2,
    )
    result = provider.generate_json(system="system", user="user")

    assert result == {"ok": True, "count": 2}
    assert seen["url"] == "https://llm.example/v1/chat/completions"
    assert seen["payload"]["model"] == "test-model"
    assert seen["payload"]["response_format"] == {"type": "json_object"}
    assert seen["timeout"] == 2

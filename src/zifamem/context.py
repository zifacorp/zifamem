"""Prompt-facing memory context."""

from __future__ import annotations

from dataclasses import dataclass, field

from zifamem.schemas import MemoryRecord, UserProfile


@dataclass(slots=True)
class MemoryContext:
    """Aggregated memory block for an agent turn."""

    l1_turns: tuple[str, ...] = ()
    l2_summaries: tuple[str, ...] = ()
    l3_memories: tuple[MemoryRecord, ...] = ()
    l4_profile: UserProfile | None = None
    procedural_rules: tuple[str, ...] = ()
    director_refs: tuple[str, ...] = ()
    section_limits: dict[str, int] = field(default_factory=lambda: {
        "l4": 600,
        "l1": 1200,
        "l2": 800,
        "l3": 1000,
        "rules": 500,
        "director": 500,
        "total": 3600,
    })

    def to_prompt(self) -> str:
        sections: list[str] = []

        profile = self.l4_profile.to_prompt_summary() if self.l4_profile else ""
        if profile:
            sections.append("[User profile]\n" + profile[: self.section_limits["l4"]])

        if self.l1_turns:
            sections.append(
                "[Current conversation]\n"
                + _join_with_limit(self.l1_turns, self.section_limits["l1"])
            )

        if self.l2_summaries:
            sections.append(
                "[Recent session summaries]\n"
                + _join_with_limit(self.l2_summaries, self.section_limits["l2"])
            )

        if self.l3_memories:
            memory_lines = tuple(
                f"- [memory | {memory.prompt_label()}] {memory.text}"
                for memory in self.l3_memories
                if memory.text.strip()
            )
            if memory_lines:
                sections.append(
                    "[Relationship memories]\n"
                    "Use these as relationship continuity and factual boundary. "
                    "Mention them only when relevant to the current turn.\n"
                    + _join_with_limit(memory_lines, self.section_limits["l3"])
                )

        if self.procedural_rules:
            sections.append(
                "[Behavior rules]\n"
                + _join_with_limit(
                    tuple(f"- {rule}" for rule in self.procedural_rules),
                    self.section_limits["rules"],
                )
            )

        if self.director_refs:
            sections.append(
                "[Active directives]\n"
                + _join_with_limit(
                    tuple(f"- {ref}" for ref in self.director_refs),
                    self.section_limits["director"],
                )
            )

        prompt = "\n\n".join(sections)
        return prompt[: self.section_limits["total"]]


def _join_with_limit(items: tuple[str, ...], limit: int) -> str:
    lines: list[str] = []
    total = 0
    for item in items:
        item = item.strip()
        if not item:
            continue
        cost = len(item) + (1 if lines else 0)
        if total + cost > limit:
            break
        lines.append(item)
        total += cost
    return "\n".join(lines)

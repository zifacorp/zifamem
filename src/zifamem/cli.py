"""Command line entry points for ZifaMem."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from zifamem.engine import ZifaMemory
from zifamem.store import JsonMemoryStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="zifamem")
    subparsers = parser.add_subparsers(dest="command")

    demo_parser = subparsers.add_parser("demo", help="Run a local companion-memory demo")
    demo_parser.add_argument(
        "--store",
        default="zifamem-demo.json",
        help="JSON file used for demo persistence",
    )

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a JSON memory store")
    inspect_parser.add_argument("store", help="Path to a JsonMemoryStore file")

    args = parser.parse_args(argv)
    if args.command == "demo":
        return _run_demo(Path(args.store))
    if args.command == "inspect":
        return _inspect_store(Path(args.store))
    parser.print_help()
    return 0


def _run_demo(path: Path) -> int:
    memory = ZifaMemory(store=JsonMemoryStore(path))
    user_id = "demo-user"
    agent_id = "zifa"
    session_id = "demo-session-1"

    memory.record_turn(
        user_id=user_id,
        agent_id=agent_id,
        session_id=session_id,
        speaker="user",
        text="My name is Mira. I like quiet check-ins before big meetings.",
    )
    memory.record_turn(
        user_id=user_id,
        agent_id=agent_id,
        session_id=session_id,
        speaker="agent",
        text="I can keep that in mind and stay brief before meetings.",
    )
    memory.record_turn(
        user_id=user_id,
        agent_id=agent_id,
        session_id=session_id,
        speaker="user",
        text="I felt anxious before today's interview, but I was proud after it ended.",
    )

    summary = memory.end_session(user_id=user_id, agent_id=agent_id, session_id=session_id)
    context = memory.get_context(
        user_id=user_id,
        agent_id=agent_id,
        query="How should you support me before interviews?",
        session_id=session_id,
    )

    print("Summary:")
    print(summary.to_prompt_text())
    print("\nPrompt context:")
    print(context.to_prompt())
    print(f"\nStore: {path}")
    return 0


def _inspect_store(path: Path) -> int:
    if not path.exists():
        raise SystemExit(f"Store not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps({
        "turns": len(data.get("turns", [])),
        "summaries": len(data.get("summaries", [])),
        "memories": len(data.get("memories", [])),
        "profiles": len(data.get("profiles", [])),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

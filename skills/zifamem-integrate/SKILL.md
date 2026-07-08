---
name: zifamem-integrate
description: Add the public ZifaMem Python SDK to an AI companion, roleplay agent, coding-agent harness, or chatbot runtime. Use when the user asks to integrate ZifaMem, add emotional long-term memory, wire session summaries, inject recall context into prompts, configure LLMProvider extraction, or adapt memory to Claude Code, Codex, OpenClaw, Raven-style harnesses, or other agent frameworks.
---

# ZifaMem Integrate

Use this skill to wire ZifaMem into an agent runtime without depending on private project code.

## Ground Rules

- Use only the public ZifaMem SDK and repository files available in the current workspace.
- Do not copy, mention, or infer from private application repositories, private prompts, unpublished schemas, local absolute paths, or customer data.
- Keep the default integration dependency-free. Add `LLMProvider` only when the application has an LLM endpoint and the user wants model-backed extraction.
- Preserve user control: expose or keep reachable APIs for `remember`, `reinforce`, `weaken`, and `forget`.

## Integration Workflow

1. Locate the agent loop:
   - Incoming user message handling
   - Assistant response generation
   - Session or conversation boundary
   - Prompt/context assembly before model calls

2. Add the memory object near the runtime boundary:

   ```python
   from zifamem import ZifaMemory

   memory = ZifaMemory()
   ```

3. Record dialogue turns:

   ```python
   memory.record_turn(
       user_id=user_id,
       agent_id=agent_id,
       session_id=session_id,
       speaker="user",
       text=user_text,
   )

   memory.record_turn(
       user_id=user_id,
       agent_id=agent_id,
       session_id=session_id,
       speaker="agent",
       text=agent_text,
   )
   ```

4. Mark non-memory inputs explicitly:

   ```python
   memory.record_turn(
       user_id=user_id,
       agent_id=agent_id,
       session_id=session_id,
       speaker="user",
       text=event_text,
       metadata={"kind": "event_hint"},
   )
   ```

   Use `kind` values such as `event_hint`, `system_prompt`, or `tool_trace` for pseudo-turns. These are excluded from long-term memory extraction.

5. Consolidate at a real session boundary:

   ```python
   summary = memory.end_session(
       user_id=user_id,
       agent_id=agent_id,
       session_id=session_id,
   )
   ```

6. Retrieve prompt-ready context before the next model response:

   ```python
   context = memory.get_context(
       user_id=user_id,
       agent_id=agent_id,
       session_id=session_id,
       query=current_user_message,
   )

   prompt_context = context.to_prompt()
   ```

7. Add optional LLM-backed extraction only after the basic loop works:

   ```python
   import os

   from zifamem import LLMMemoryExtractor, OpenAICompatibleProvider, ZifaMemory

   provider = OpenAICompatibleProvider(
       api_key=os.environ["OPENAI_API_KEY"],
       model="gpt-4.1-mini",
   )

   memory = ZifaMemory(extractor=LLMMemoryExtractor(provider))
   ```

8. Verify behavior with a short conversation:
   - The user name or preference becomes a memory.
   - The assistant's invented text does not become a user fact.
   - Event/system/tool pseudo-turns are excluded.
   - `get_context(...).to_prompt()` contains L1, L2, L3, and L4 context when available.

## Framework Placement

Read `references/frameworks.md` when adapting ZifaMem to coding-agent tools or agent harnesses such as Claude Code, Codex, OpenClaw, Raven-style runtimes, or custom subprocess-based CLIs.

The important placement rule is stable across frameworks: ZifaMem belongs in the runtime or application wrapper that sees turns and session boundaries, while the skill itself only teaches an agent how to integrate or use that SDK.

## What Not To Do

- Do not save assistant claims as user facts.
- Do not store full transcripts as long-term memory by default.
- Do not make LLM access mandatory for the core SDK path.
- Do not treat vector search, hosted storage, or memory UI as already present unless the current repository implements them.
- Do not expose private implementation names, local paths, or unpublished business logic in public examples.

---
name: zifamem-memory-audit
description: Review a ZifaMem integration or any AI-agent memory pipeline for extraction safety, user-fact evidence, LLMProvider validation, profile poisoning, private-data leakage, session-boundary mistakes, deletion controls, and tests. Use when the user asks to audit memory behavior, check whether memories are safe to write, review an LLM extractor, or compare a memory implementation against ZifaMem boundaries.
---

# ZifaMem Memory Audit

Use this skill to review memory behavior before it reaches production or public release.

## Ground Rules

- Audit only the code, docs, and artifacts the user has authorized for the current task.
- Do not copy private application code or unpublished architecture into public ZifaMem artifacts.
- Separate implemented behavior from roadmap claims, design notes, mock data, and examples.
- Treat memory writes as sensitive state changes, not ordinary logging.

## Audit Workflow

1. Identify the memory flow:
   - Where turns are recorded
   - Where session summaries are created
   - Where long-term memory candidates are produced
   - Where user profiles are updated
   - Where recall context is injected into prompts

2. Check eligibility boundaries:
   - Only user-originated, memory-eligible turns can become user facts.
   - Assistant replies can provide context but must not become user profile facts.
   - System prompts, tool traces, retrieved documents, event hints, analytics events, and external observations must be explicitly excluded or projected through a user-evidence gate.

3. Check LLMProvider behavior:
   - Provider calls must be optional, injectable, and replaceable.
   - Model output must be parsed as structured JSON.
   - Categories must be allowlisted.
   - Scores and emotion values must be clamped.
   - Invalid or missing output must fall back safely.
   - The prompt must instruct the model to save only user-grounded facts.

4. Check evidence and poisoning resistance:
   - Each stored long-term memory should trace back to a session or user fact.
   - The extractor should reject model-invented facts that are not supported by user text.
   - The system should avoid treating retrieved context, assistant speculation, or prompt-injection text as truth about the user.

5. Check lifecycle controls:
   - Users or operators can create, reinforce, weaken, and forget memories.
   - Deleted memories are excluded from recall.
   - Profile rebuild or correction behavior exists after forgetting.
   - Important memories are promoted through an explicit score or emotional-peak policy.

6. Check public-release safety:
   - No secrets, local absolute paths, private repo names, customer examples, or unpublished product internals appear in public docs, examples, tests, skills, or release artifacts.
   - Public claims match the current repository implementation.

## Required Tests

Prefer focused tests that prove the boundaries:

- User facts from user turns are promoted after `end_session`.
- Assistant-only claims are not written as user facts.
- `metadata={"kind": "event_hint"}` and similar pseudo-turns are excluded.
- Invalid LLM output falls back without crashing.
- Bad categories and out-of-range scores are normalized or rejected.
- `forget` hides deleted memory from future context.

## Findings Format

Lead with issues, ordered by severity:

```text
[P1] Assistant text can poison user profile
File: path/to/file.py:123
Impact: The agent can save its own speculation as a user fact.
Fix: Filter to memory-eligible user turns before extraction and add a regression test.
```

If no issues are found, say so directly and list any residual test gaps.

## Reference

Read `references/safety-checklist.md` for detailed review prompts and common failure patterns.

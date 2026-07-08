# ZifaMem Memory Safety Checklist

Use this checklist during implementation review, PR review, or release review.

## Data Boundary

- Are user turns, assistant turns, system prompts, tool traces, events, and retrieved documents represented separately?
- Can a non-user event accidentally be recorded as `speaker="user"`?
- Does the code support `metadata={"memory_eligible": False}` for sensitive turns?
- Are `event_hint`, `system_prompt`, and `tool_trace` excluded before long-term extraction?

## Extraction Boundary

- Is extraction performed at a session boundary instead of every token or every raw event?
- Does the extractor use only memory-eligible user text for user facts?
- Are assistant messages allowed only as context, never as user facts?
- Is there a deterministic fallback when LLM extraction fails?

## LLMProvider Boundary

- Is the provider injected through an interface instead of hard-coded?
- Can the SDK run without provider credentials?
- Is the provider response parsed as a JSON object?
- Are invalid JSON, network failure, and missing fields handled safely?
- Are category values allowlisted?
- Are importance, strength, valence, arousal, intensity, trust, and comfort values clamped?
- Does memory creation reject facts that lack user evidence?

## Profile Boundary

- Are identity fields guarded against low-evidence overwrites?
- Are preferences and relationship notes deduplicated?
- Does profile update skip invalid or empty values?
- Does forgetting a memory rebuild or correct the profile?

## Recall Boundary

- Does recall exclude deleted memories?
- Does ranking balance semantic relevance, strength, importance, and emotional intensity?
- Does prompt context clearly separate current conversation, summaries, relationship memories, and user profile?

## Public Release Boundary

- Search for private paths and repo names before release.
- Search for secrets and API keys before release.
- Search docs, tests, examples, and skills for private prompts or internal-only architecture.
- Verify public claims against source files, not design notes.

## Suggested Searches

Run targeted searches before public release:

```bash
rg -n "private-repo-name|/Users/|OPENAI_API_KEY=.*|ANTHROPIC_API_KEY=.*|sk-|password|secret" .
rg -n "system_prompt|tool_trace|event_hint|memory_eligible|LLMProvider|OpenAICompatibleProvider" src tests skills README.md docs
```

Ignore known external reference folders only when they are intentionally untracked and out of release scope.

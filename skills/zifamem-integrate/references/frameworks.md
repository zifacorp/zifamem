# Framework Notes

Use these notes when adapting ZifaMem to a coding-agent tool or agent harness.

## Portable Skill Package

This skill uses the portable core of the Agent Skills pattern:

- A folder per skill
- A required `SKILL.md`
- YAML frontmatter with `name` and `description`
- Plain Markdown instructions
- Optional references

Avoid tool-specific frontmatter, dynamic shell injection, and pre-approved tool lists unless the user explicitly wants a tool-specific variant.

## Claude Code

Install by copying or symlinking the skill folder to one of these locations:

- Personal: `~/.claude/skills/<skill-name>/SKILL.md`
- Project: `.claude/skills/<skill-name>/SKILL.md`

Use project skills when the ZifaMem integration belongs to one repository. Use personal skills when the user wants the skill available across projects.

## Codex

Install by copying or symlinking the skill folder to one of these locations:

- Personal: `~/.codex/skills/<skill-name>/SKILL.md`
- Repository-scoped: `.agents/skills/<skill-name>/SKILL.md`

Keep repository-scoped skills public-safe because they may be committed with the project.

## OpenClaw And Similar Tools

Use the same folder shape when the tool supports Agent Skills or `SKILL.md` packages. Copy the folder into that tool's configured skills directory. Common local setups use a directory similar to `~/.openclaw/skills/`, but verify the user's installed runtime before editing their machine.

## Raven-Style Harnesses

Treat ZifaMem as a memory substrate inside the runtime layer:

1. The harness receives messages from CLI, TUI, gateway, or chat channels.
2. The runtime records user and agent turns into ZifaMem.
3. The runtime calls `end_session` when a session boundary is reached.
4. The runtime calls `get_context` before model generation.
5. Skills remain procedural guidance; they do not replace the actual memory store.

## Subprocess Coding Agents

For wrappers that launch Claude Code, Codex, Gemini CLI, OpenClaw, OpenCode, or another coding CLI as a subprocess, do not inject ZifaMem into the child process unless that child exposes a stable plugin or MCP interface. Prefer a parent runtime that:

- Captures user prompts and agent outputs
- Stores or recalls memory outside the child CLI
- Adds recalled memory to the prompt or task brief
- Keeps deletion and consent controls in the parent application

## Decision Rules

- If the user asks for a public skill: create a portable `SKILL.md` package.
- If the user asks for live memory inside an app: integrate the Python SDK in the app runtime.
- If the user asks for external tool access: consider an MCP server or plugin, not only a skill.
- If the user asks for a marketplace bundle: keep the skill portable first, then add tool-specific packaging separately.

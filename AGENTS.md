# Repository Guidelines

## Project Structure & Module Organization

This repository now contains an alpha Python SDK for ZifaMem.

- `README.md` is the canonical English project overview and roadmap.
- `src/zifamem/` contains the Python SDK implementation.
- `examples/` contains runnable SDK examples.
- `tests/` contains the unit test suite.
- `docs/i18n/` contains localized README-style documents, named by locale such as `zh-CN.md`, `ja.md`, and `pt.md`.
- `assets/` contains static images used by the README and translations, including `zifamem-banner.png`.

Keep runtime code under `src/zifamem/`, examples under `examples/`, and tests under `tests/`.

## Build, Test, and Development Commands

Useful commands:

- `git status --short` checks pending changes before editing.
- `rg --files` lists tracked project files quickly.
- `python -m pip install -e .` installs the SDK locally.
- `python -m zifamem demo` runs the local JSON-backed demo.
- `python -m pip install -e ".[dev]"` installs test dependencies.
- `python -m pytest` runs the unit test suite.
- `markdownlint README.md docs/i18n/*.md` checks Markdown style if `markdownlint` is installed.

Do not add dependency installation steps unless the matching manifest, lockfile, and documented command are also committed.

## Coding Style & Naming Conventions

Keep Markdown concise, scannable, and consistent with `README.md`. Use sentence-case prose, descriptive headings, and short paragraphs. Preserve the centered HTML blocks in README-style files when updating language switchers, badges, or hero images.

Python code should be typed where practical, dependency-light, and safe to run without external services. Prefer explicit dataclasses and storage interfaces over hidden global state.

Use locale filenames in `docs/i18n/` with BCP 47-style casing, for example `zh-CN.md`, `ko.md`, or `es.md`. Asset filenames should be lowercase, hyphen-separated, and descriptive, for example `zifamem-banner.png`.

## Testing Guidelines

Run `python -m pytest` for code changes. For documentation changes, manually verify links, images, language switcher targets, and Mermaid diagrams. Add tests alongside new implementation behavior.

## Commit & Pull Request Guidelines

Recent commits use short imperative messages such as `Add localized README translations` and `Polish project README`. Follow that pattern: start with an action verb, keep the subject specific, and avoid noisy prefixes.

Pull requests should include a concise summary, the affected files or locales, and screenshots when README visuals or assets change. Link related issues when available, and call out any new commands, dependencies, or generated files.

## Security & Configuration Tips

Do not commit secrets, private prompts, unpublished implementation details, or local metadata such as `.DS_Store`. Keep public claims aligned with the current project status: this is an alpha SDK, not a production hosted memory service.

# Claude Extract NI

> Non-interactive CLI for extracting, searching, and backing up Claude Code conversations. Optimized for Claude Code agent automation.

**The ONLY tool to export Claude Code conversations** — natively non-interactive, zero prompts, scriptable from any automation context.

## Install

```bash
pip install git+https://github.com/MiaouLeChat929/claude-conversation-extractor.git --break-system-packages

# or with uv
uv pip install git+https://github.com/MiaouLeChat929/claude-conversation-extractor.git --system
```

For development, clone and install editable:
```bash
git clone https://github.com/MiaouLeChat929/claude-conversation-extractor.git
cd claude-conversation-extractor
pip install -e . --break-system-packages
```

## Core Commands

List sessions (numbered by recency, 1 = most recent):
```bash
claude-extract --list
claude-extract --list --limit 20
```

Extract specific sessions:
```bash
claude-extract --extract 1
claude-extract --extract 1,3,5
```

Extract recent or all sessions:
```bash
claude-extract --recent 5
claude-extract --all
```

## Search — Always Auto-Extracts

Search finds matches and automatically extracts them. No confirmation prompts:

```bash
claude-extract --search "anki"
claude-extract --search "redis" --output ~/Desktop/anki/conversations
claude-extract --search "error handling" --format json
```

Regex search:
```bash
claude-extract --search-regex "import.*re"
```

Search filters:
- `--search-date-from YYYY-MM-DD` — filter by start date
- `--search-date-to YYYY-MM-DD` — filter by end date
- `--search-speaker {human,assistant,both}` — filter by speaker
- `--case-sensitive` — case-sensitive search

## Output Control

Specify output directory:
```bash
claude-extract --output ~/my-logs --extract 1
```

Choose format (markdown, json, or html):
```bash
claude-extract --format json --extract 1
claude-extract --format html --extract 1
```

Include tool calls and system messages with `--detailed`.

## Common Patterns

Archive all conversations from a specific period:
```bash
claude-extract --search-date-from 2026-01-01 --search-date-to 2026-03-31 --all --output ~/archive
```

Find and extract all sessions about a topic:
```bash
claude-extract --search "anki" --output ~/Desktop/anki/conversations
```

Get JSON exports for programmatic processing:
```bash
claude-extract --search "architecture" --format json --output ~/data
```

## Session ID Behavior

Session IDs are **ephemeral** — they reflect current recency order, not persisted identifiers. After deletion of old sessions, IDs shift. Always run `--list` to get current session numbers before extracting.

## Error Recovery

Session not found — run list first to get current valid IDs, then retry:
```bash
claude-extract --list
claude-extract --extract 2
```

Output directory issues — ensure the directory exists:
```bash
mkdir -p ~/my-logs && claude-extract --output ~/my-logs --extract 1
```

## How It Works

1. Locates Claude Code logs in `~/.claude/projects/`
2. Parses undocumented JSONL format
3. Extracts conversations as clean Markdown, JSON, or HTML
4. Search indexes content for instant searching

## Privacy

- 100% Local — never sends conversations anywhere
- No internet required
- Read-only — never modifies Claude Code files
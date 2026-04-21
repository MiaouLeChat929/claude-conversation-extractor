# Claude Extract NI — Development Guide

## Installation

Clone and install in editable mode:
```bash
git clone https://github.com/MiaouLeChat929/claude-conversation-extractor.git
cd claude-conversation-extractor
pip install -e . --break-system-packages
```

Verify the commands are available:
```bash
claude-extract --help
claude-search --help
```

## Repository Structure

```
src/
├── extract_claude_logs.py  # Main CLI (--list, --extract, --search, --all, etc.)
├── search_conversations.py # ConversationSearcher — non-interactive search engine
└── search_cli.py          # Standalone search CLI wrapper
```

## Key Design Principles

- **Natively non-interactive**: Zero prompts. Every operation completes in one shot.
- **Search always auto-extracts**: `claude-extract --search "term"` finds matches and extracts all of them automatically.
- **No interactive fallback**: If you need to browse interactively, use the parent project `claude-conversation-extractor`.

## Adding Features

### To `extract_claude_logs.py`

The `ClaudeConversationExtractor` class is the core. Methods to know:
- `find_sessions()` — returns `List[Path]` of all `chat_*.jsonl` files
- `extract_conversation(path, detailed=False)` — returns `List[Dict[str, str]]` of messages
- `save_as_markdown/json/html(conversation, session_id)` — writes to disk

The `main()` function handles argparse and dispatch. Search flow is at lines ~687–765 — it groups results by file then auto-extracts.

### To `search_conversations.py`

`ConversationSearcher.search()` returns `List[SearchResult]`. Each result has `file_path`, `matched_content`, `context`, `speaker`, `timestamp`, `relevance_score`.

## Running Tests

Install dev dependencies and run pytest:
```bash
pip install -e ".[dev]" --break-system-packages
pytest
```

## Before Committing

Verify these commands all succeed without prompts:
1. `claude-extract --list`
2. `claude-extract --search "test"`
3. `claude-extract --extract 1 --output /tmp/test_extract`

## Building a Distribution

```bash
pip install build
python -m build
```
#!/usr/bin/env python3
"""
Non-interactive search CLI for Claude conversations.
All searches auto-extract matching sessions — no prompts.
"""

import argparse
import sys


def main():
    """Main entry point for CLI search."""
    parser = argparse.ArgumentParser(
        description="Search and extract Claude Code conversations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "python error"              # Search and extract matches
  %(prog)s --search "redis"            # Search and extract matches
  %(prog)s --search "anki" --output /tmp/results
  %(prog)s --search "error" --format json
  %(prog)s --search "refactor" --detailed
        """
    )
    parser.add_argument("search_term", nargs="?", help="Search term")
    parser.add_argument("--search", dest="search_term", help="Search term (alternative)")
    parser.add_argument("--output", "-o", help="Output directory for extractions")
    parser.add_argument("--format", choices=["markdown", "json", "html"],
        default="markdown", help="Output format (default: markdown)")
    parser.add_argument("--detailed", action="store_true",
        help="Include tool use and system messages")
    parser.add_argument("--limit", type=int, default=20,
        help="Max search results (default: 20)")
    parser.add_argument("--case-sensitive", action="store_true",
        help="Make search case-sensitive")

    args = parser.parse_args()

    # Get search term
    if not args.search_term:
        if not sys.stdin.isatty():
            args.search_term = sys.stdin.read().strip()
        else:
            print("❌ No search term provided")
            return

    if not args.search_term:
        print("❌ No search term provided")
        return

    # Imports here so they're not loaded for --help
    try:
        from search_conversations import ConversationSearcher
        from extract_claude_logs import ClaudeConversationExtractor
    except ImportError:
        from .search_conversations import ConversationSearcher
        from .extract_claude_logs import ClaudeConversationExtractor

    print(f"\n🔍 Searching for: '{args.search_term}'")
    print("=" * 60)

    searcher = ConversationSearcher()
    extractor = ClaudeConversationExtractor(args.output)

    results = searcher.search(args.search_term, max_results=args.limit)

    if not results:
        print(f"\n❌ No matches found for '{args.search_term}'")
        return

    # Group by file
    by_file = {}
    for result in results:
        fname = result.file_path.name
        if fname not in by_file:
            by_file[fname] = []
        by_file[fname].append(result)

    print(f"\n✅ Found {len(results)} matches across {len(by_file)} conversations")

    # Get unique session paths
    session_paths = []
    sessions_meta = []
    all_sessions = extractor.find_sessions()

    for fname, file_results in by_file.items():
        session_id = fname.replace('.jsonl', '')
        sessions_meta.append((fname, session_id))

        for session_path in all_sessions:
            if session_path.name == fname:
                session_paths.append(session_path)
                break

    print(f"\n📤 Extracting {len(session_paths)} matching sessions...")

    for i, (session_path, (fname, sid)) in enumerate(zip(session_paths, sessions_meta), 1):
        conversation = extractor.extract_conversation(session_path, detailed=args.detailed)
        if conversation:
            if args.format == "json":
                output = extractor.save_as_json(conversation, sid)
            elif args.format == "html":
                output = extractor.save_as_html(conversation, sid)
            else:
                output = extractor.save_as_markdown(conversation, sid)
            print(f"✅ {i}/{len(session_paths)}: {output.name}")
        else:
            print(f"⏭️  Skipped session {i} (no conversation)")


if __name__ == "__main__":
    main()

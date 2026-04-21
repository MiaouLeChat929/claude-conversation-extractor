#!/usr/bin/env python3
"""
Simple CLI search for Claude conversations without terminal control.
This is used when running `claude-search-ni` from the command line.
Supports non-interactive flags for scripting and agent usage.
"""

import argparse
import sys

# Handle both package and direct execution imports
try:
    from .search_conversations import ConversationSearcher
    from .extract_claude_logs import ClaudeConversationExtractor
except ImportError:
    # Fallback for direct execution or when not installed as package
    from search_conversations import ConversationSearcher
    from extract_claude_logs import ClaudeConversationExtractor


def main():
    """Main entry point for CLI search."""
    parser = argparse.ArgumentParser(
        description="Search Claude Code conversations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "python error"               # Search for term (interactive)
  %(prog)s --search "redis"            # Search for term
  %(prog)s --search "error" --extract-matching --output /tmp/results
  %(prog)s --search "anki" --json-output
        """
    )
    parser.add_argument("search_term", nargs="?", help="Search term")
    parser.add_argument("--search", dest="search_term", help="Search term (alternative)")
    parser.add_argument("--non-interactive", "-y", action="store_true",
        help="Skip all prompts, auto-confirm extractions")
    parser.add_argument("--extract-matching", action="store_true",
        help="Auto-extract all matching sessions")
    parser.add_argument("--output", "-o", help="Output directory for extractions")
    parser.add_argument("--format", choices=["markdown", "json", "html"],
        default="markdown", help="Output format (default: markdown)")
    parser.add_argument("--json-output", action="store_true",
        help="Output machine-readable JSON")
    parser.add_argument("--detailed", action="store_true",
        help="Include tool use and system messages")
    parser.add_argument("--limit", type=int, default=20,
        help="Max search results (default: 20)")

    args = parser.parse_args()

    # Get search term
    if not args.search_term:
        if not sys.stdin.isatty():
            # Piped input
            args.search_term = sys.stdin.read().strip()
        else:
            try:
                args.search_term = input("🔍 Enter search term: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Search cancelled")
                return

    if not args.search_term:
        print("❌ No search term provided")
        return

    print(f"\n🔍 Searching for: '{args.search_term}'")
    print("=" * 60)

    # Initialize searcher
    searcher = ConversationSearcher()
    extractor = ClaudeConversationExtractor(args.output)

    # Perform search
    results = searcher.search(args.search_term, max_results=args.limit)

    if not results:
        print(f"\n❌ No matches found for '{args.search_term}'")
        print("\n💡 Tips:")
        print("   - Try a more general search term")
        print("   - Search is case-insensitive by default")
        print("   - Partial matches are included")
        return

    # Group by file
    by_file = {}
    for result in results:
        fname = result.file_path.name
        if fname not in by_file:
            by_file[fname] = []
        by_file[fname].append(result)

    # Get unique session paths
    session_paths = []
    sessions_meta = []
    all_sessions = extractor.find_sessions()

    for fname, file_results in by_file.items():
        session_id = fname.replace('.jsonl', '')
        sessions_meta.append((fname, session_id))

        # Find the actual file path
        for session_path in all_sessions:
            if session_path.name == fname:
                session_paths.append(session_path)
                break

    # JSON output mode (no extraction)
    if args.json_output and not args.extract_matching:
        import json
        search_results = []
        for fname, file_results in by_file.items():
            search_results.append({
                "session_id": fname.replace('.jsonl', ''),
                "match_count": len(file_results),
                "matches": [
                    {
                        "speaker": r.speaker,
                        "content": r.matched_content[:200],
                        "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    }
                    for r in file_results[:3]
                ]
            })
        print(json.dumps({
            "status": "success",
            "query": args.search_term,
            "matches": search_results
        }, indent=2))
        return

    # Display results
    print(f"\n✅ Found {len(results)} results across {len(session_paths)} conversations:\n")
    for i, (fname, file_results) in enumerate(by_file.items(), 1):
        session_id = fname.replace('.jsonl', '')
        print(f"{i}. Session {session_id[:8]}... ({len(file_results)} matches)")
        first = file_results[0]
        preview = first.matched_content[:150].replace('\n', ' ')
        print(f"   {first.speaker}: {preview}...")
        print()

    # Auto-extract mode
    if args.extract_matching or args.non_interactive:
        print(f"\n📤 Auto-extracting {len(session_paths)} matching sessions...")
        import json
        extracted = []
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
                extracted.append({
                    "session_id": sid,
                    "output_file": str(output),
                    "message_count": len(conversation)
                })
            else:
                print(f"⏭️  Skipped session {i} (no conversation)")
        if args.json_output:
            print(json.dumps({"status": "success", "extracted": extracted}, indent=2))
        return

    # Interactive mode
    if session_paths:
        print("\n" + "=" * 60)
        print("Options:")
        print("  V. VIEW a conversation")
        print("  E. EXTRACT all conversations")
        print("  Q. QUIT")

        try:
            choice = input("\nYour choice: ").strip().upper()

            if choice == 'V':
                if len(session_paths) == 1:
                    extractor.display_conversation(session_paths[0])
                    extract_choice = input("\n📤 Extract this conversation? (y/N): ").strip().lower()
                    if extract_choice == 'y':
                        conversation = extractor.extract_conversation(session_paths[0], detailed=args.detailed)
                        if conversation:
                            output = extractor.save_as_markdown(conversation, sessions_meta[0][1])
                            print(f"✅ Saved: {output.name}")
                else:
                    print("\nSelect conversation to view:")
                    for i, (fname, sid) in enumerate(sessions_meta, 1):
                        print(f"  {i}. {sid[:8]}...")

                    try:
                        view_num = int(input("\nEnter number (1-{}): ".format(len(sessions_meta))))
                        if 1 <= view_num <= len(session_paths):
                            extractor.display_conversation(session_paths[view_num - 1])
                            extract_choice = input("\n📤 Extract this conversation? (y/N): ").strip().lower()
                            if extract_choice == 'y':
                                conversation = extractor.extract_conversation(session_paths[view_num - 1], detailed=args.detailed)
                                if conversation:
                                    output = extractor.save_as_markdown(conversation, sessions_meta[view_num - 1][1])
                                    print(f"✅ Saved: {output.name}")
                    except (ValueError, IndexError):
                        print("❌ Invalid selection")

            elif choice == 'E':
                for i, (session_path, (fname, sid)) in enumerate(zip(session_paths, sessions_meta), 1):
                    print(f"\n📤 Extracting session {i}...")
                    conversation = extractor.extract_conversation(session_path, detailed=args.detailed)
                    if conversation:
                        output = extractor.save_as_markdown(conversation, sid)
                        print(f"✅ Saved: {output.name}")

            elif choice == 'Q':
                print("\n👋 Goodbye!")

        except (EOFError, KeyboardInterrupt):
            print("\n👋 Search cancelled")


if __name__ == "__main__":
    main()
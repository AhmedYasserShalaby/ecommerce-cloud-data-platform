from __future__ import annotations

import argparse

from commerce_platform.generator import generate_batch
from commerce_platform.gold import run_gold
from commerce_platform.silver import run_silver
from commerce_platform.streaming import consume_stream_events, produce_stream_events


def main() -> None:
    parser = argparse.ArgumentParser(prog="commerce-platform")
    parser.add_argument("--version", action="store_true", help="Print version and exit.")
    subparsers = parser.add_subparsers(dest="command")

    for name in ["generate-batch", "stream-produce", "stream-consume", "run-spark", "run-dbt", "run-quality", "run-all", "smoke"]:
        command = subparsers.add_parser(name)
        command.add_argument("--profile", default="ci", choices=["ci", "demo", "full"])
        if name == "stream-produce":
            command.add_argument("--events", type=int, default=250)
        if name == "stream-consume":
            command.add_argument("--max-events", type=int, default=None)

    args = parser.parse_args()
    if args.version:
        from commerce_platform import __version__

        print(__version__)
        return
    if not args.command:
        parser.print_help()
        return

    if args.command == "generate-batch":
        manifest = generate_batch(args.profile)
        print(f"Generated batch profile={args.profile} at {manifest['batch_dir']}")
        return
    if args.command == "stream-produce":
        result = produce_stream_events(args.profile, event_count=args.events)
        print(f"Produced stream events: {result}")
        return
    if args.command == "stream-consume":
        result = consume_stream_events(args.profile, max_events=args.max_events)
        print(f"Consumed stream events: {result}")
        return
    if args.command == "run-spark":
        counts = run_silver(args.profile)
        print(f"Built silver profile={args.profile}: {counts}")
        return
    if args.command == "run-dbt":
        counts = run_gold(args.profile)
        print(f"Built gold profile={args.profile}: {counts}")
        return

    raise SystemExit(f"{args.command} is not implemented yet.")


if __name__ == "__main__":
    main()

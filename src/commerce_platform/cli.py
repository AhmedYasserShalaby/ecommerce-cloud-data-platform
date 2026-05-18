from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(prog="commerce-platform")
    parser.add_argument("--version", action="store_true", help="Print version and exit.")
    subparsers = parser.add_subparsers(dest="command")

    for name in [
        "generate-batch",
        "stream-produce",
        "stream-consume",
        "run-spark",
        "run-dbt",
        "run-quality",
        "run-all",
        "smoke",
    ]:
        command = subparsers.add_parser(name)
        command.add_argument("--profile", default="ci", choices=["ci", "demo", "full"])

    args = parser.parse_args()
    if args.version:
        from commerce_platform import __version__

        print(__version__)
        return
    if not args.command:
        parser.print_help()
        return

    raise SystemExit(f"{args.command} is not implemented yet.")


if __name__ == "__main__":
    main()

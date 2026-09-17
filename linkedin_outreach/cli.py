from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from . import csv_import, pipeline
from .config import db_path, load_icp_config, load_sequence_config
from .store import LeadStore


def cmd_prospect(args: argparse.Namespace) -> None:
    icp = load_icp_config(args.icp)
    store = LeadStore(db_path())
    count = pipeline.prospect(store, icp)
    print(f"prospected {count} leads for ICP '{icp.name}'")


def cmd_import_csv(args: argparse.Namespace) -> None:
    store = LeadStore(db_path())
    count = csv_import.import_csv(store, args.path)
    print(f"imported {count} leads from {args.path}")


def cmd_score(args: argparse.Namespace) -> None:
    icp = load_icp_config(args.icp)
    store = LeadStore(db_path())
    results = pipeline.score_all(store, icp)
    print(f"qualified={results['qualified']} disqualified={results['disqualified']}")


def cmd_sequence(args: argparse.Namespace) -> None:
    sequence = load_sequence_config(args.sequence)
    store = LeadStore(db_path())
    count = pipeline.generate_sequences(store, sequence, args.out)
    print(f"generated sequences for {count} qualified leads -> {args.out}")


def cmd_sync(args: argparse.Namespace) -> None:
    store = LeadStore(db_path())
    results = pipeline.sync_hubspot(store)
    print(f"synced={results['synced']} skipped_no_email={results['skipped_no_email']}")


def cmd_status(args: argparse.Namespace) -> None:
    store = LeadStore(db_path())
    counts = store.funnel_counts()
    total = sum(counts.values())
    print(f"total leads: {total}")
    for status in ("new", "qualified", "disqualified", "sequenced", "synced"):
        print(f"  {status:<14} {counts.get(status, 0)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="outreach", description="LinkedIn outreach lead engine")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prospect", help="search Apollo.io for leads matching an ICP")
    p.add_argument("--icp", required=True, help="path to ICP config yaml")
    p.set_defaults(func=cmd_prospect)

    p = sub.add_parser("import-csv", help="import leads from an Apollo-style CSV export")
    p.add_argument("--path", required=True, help="path to CSV file")
    p.set_defaults(func=cmd_import_csv)

    p = sub.add_parser("score", help="score new leads against an ICP")
    p.add_argument("--icp", required=True, help="path to ICP config yaml")
    p.set_defaults(func=cmd_score)

    p = sub.add_parser("sequence", help="generate personalized message copy for qualified leads")
    p.add_argument("--sequence", required=True, help="path to sequence config yaml")
    p.add_argument("--out", default="outreach_messages.csv", help="output CSV path")
    p.set_defaults(func=cmd_sequence)

    p = sub.add_parser("sync", help="push sequenced leads to HubSpot as contacts")
    p.set_defaults(func=cmd_sync)

    p = sub.add_parser("status", help="show pipeline funnel counts")
    p.set_defaults(func=cmd_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

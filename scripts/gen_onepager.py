#!/usr/bin/env python3
"""
Generate One-Pager using config and shared services
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

from pefc.config.loader import get_config
from pefc.logging import setup_logging
from pefc.onepager.render import build_onepager


def main():
    """Main function."""
    ap = argparse.ArgumentParser(description="Generate one-pager markdown")
    ap.add_argument("--config", default=None, help="Path to config file")
    ap.add_argument("--json-logs", action="store_true", help="Enable JSON logging")
    args = ap.parse_args()

    setup_logging(json=args.json_logs)

    try:
        cfg = get_config(path=args.config)
        out = build_onepager(cfg, out_dir=Path(cfg.pack.out_dir))
        print(str(out))
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

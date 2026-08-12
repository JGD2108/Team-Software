"""Explicit, idempotent PMP source-load command.

This command is the only normal operational path that reads JOSE.xlsx.  The
dashboard and order endpoints query the persisted PMP tables instead.
"""

import argparse
import json
from pathlib import Path

from app.core.database import SessionLocal
from app.services.pmp import default_jose_path, import_jose_workbook, import_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Load JOSE.xlsx into persistent PMP tables")
    parser.add_argument("--source", type=Path, default=default_jose_path(), help="Path to the approved JOSE.xlsx source")
    args = parser.parse_args()

    with SessionLocal() as db:
        imported = import_jose_workbook(db, args.source)
        print(json.dumps(import_summary(db, imported), ensure_ascii=False, default=str, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

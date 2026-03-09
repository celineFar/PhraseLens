#!/usr/bin/env python3
"""Add `run_notes` column to manual_tests run_history CSV files."""

from __future__ import annotations

import csv
from pathlib import Path


BASE_FIELDS = [
    "run_id",
    "generated_at_utc",
    "dataset_id",
    "split_id",
    "gold",
    "predicted",
    "tp",
    "fp",
    "fn",
    "precision",
    "recall",
    "f1",
    "predictions_csv",
    "report_md",
    "metrics_json",
]
TARGET_FIELDS = BASE_FIELDS + ["run_notes"]


def migrate_file(path: Path) -> bool:
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return False
        if "run_notes" in reader.fieldnames:
            return False
        rows = list(reader)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TARGET_FIELDS)
        writer.writeheader()
        for row in rows:
            out = {k: row.get(k, "") for k in TARGET_FIELDS}
            out["run_notes"] = ""
            writer.writerow(out)
    return True


def main() -> None:
    root = Path("manual_tests/datasets")
    files = sorted(root.glob("*/**/run_history.csv"))
    changed = 0
    for path in files:
        if migrate_file(path):
            changed += 1
            print(f"migrated: {path.as_posix()}")
        else:
            print(f"unchanged: {path.as_posix()}")
    print(f"done: {changed} migrated, {len(files) - changed} unchanged")


if __name__ == "__main__":
    main()

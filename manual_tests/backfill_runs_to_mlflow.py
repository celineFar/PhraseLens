#!/usr/bin/env python3
"""Backfill historical manual test runs into MLflow from run_history.csv."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import mlflow
from mlflow.tracking import MlflowClient


def _existing_run_ids(client: MlflowClient, experiment_id: str) -> set[str]:
    existing: set[str] = set()
    page_token: str | None = None
    while True:
        page = client.search_runs(
            experiment_ids=[experiment_id],
            filter_string="tags.component = 'manual_tests'",
            max_results=500,
            page_token=page_token,
        )
        for run in page:
            run_id = run.data.tags.get("run_id")
            if run_id:
                existing.add(run_id)
        page_token = page.token
        if not page_token:
            break
    return existing


def _to_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill manual test runs to MLflow.")
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--split-id", required=True)
    parser.add_argument("--output-root", default="manual_tests")
    parser.add_argument("--mlflow-tracking-uri", default="")
    parser.add_argument("--mlflow-experiment", default="manual_tests")
    parser.add_argument(
        "--include-existing",
        action="store_true",
        help="Also import run_ids that already exist in MLflow.",
    )
    args = parser.parse_args()

    output_root = Path(args.output_root)
    case_dir = output_root / "datasets" / args.dataset_id / args.split_id
    history_path = case_dir / "run_history.csv"
    if not history_path.exists():
        raise FileNotFoundError(f"run_history.csv not found: {history_path}")

    tracking_uri = args.mlflow_tracking_uri or f"file:{(output_root / 'mlruns').resolve().as_posix()}"
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(args.mlflow_experiment)

    client = MlflowClient()
    experiment = client.get_experiment_by_name(args.mlflow_experiment)
    if experiment is None:
        raise RuntimeError(f"MLflow experiment not found: {args.mlflow_experiment}")

    existing_ids = set()
    if not args.include_existing:
        existing_ids = _existing_run_ids(client, experiment.experiment_id)

    imported = 0
    skipped = 0
    with history_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            run_id = row.get("run_id", "").strip()
            if not run_id:
                continue
            if run_id in existing_ids:
                skipped += 1
                continue

            run_name = f"backfill_{run_id}"
            with mlflow.start_run(run_name=run_name):
                tags = {
                    "component": "manual_tests",
                    "dataset": row.get("dataset_id", args.dataset_id),
                    "split": row.get("split_id", args.split_id),
                    "run_id": run_id,
                    "generated_at_utc": row.get("generated_at_utc", ""),
                    "run_notes": row.get("run_notes", ""),
                    "backfilled": "true",
                }
                mlflow.set_tags({k: str(v) for k, v in tags.items()})
                mlflow.log_params(
                    {
                        "dataset_id": row.get("dataset_id", args.dataset_id),
                        "split_id": row.get("split_id", args.split_id),
                        "source_desc": "historical_backfill",
                        "run_notes": row.get("run_notes", ""),
                    }
                )
                mlflow.log_metrics(
                    {
                        "gold": _to_float(row.get("gold")),
                        "predicted": _to_float(row.get("predicted")),
                        "tp": _to_float(row.get("tp")),
                        "fp": _to_float(row.get("fp")),
                        "fn": _to_float(row.get("fn")),
                        "precision": _to_float(row.get("precision")),
                        "recall": _to_float(row.get("recall")),
                        "f1": _to_float(row.get("f1")),
                    }
                )
                for key in ("predictions_csv", "report_md", "metrics_json"):
                    path_str = row.get(key, "").strip()
                    if not path_str:
                        continue
                    path = Path(path_str)
                    if path.exists():
                        mlflow.log_artifact(path.as_posix())

            imported += 1

    print(
        f"Backfill complete. Imported={imported}, Skipped={skipped}, "
        f"Experiment={args.mlflow_experiment}, TrackingURI={tracking_uri}"
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run MWE evaluation against manual gold with organized run outputs."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.nlp.pipeline import get_nlp, lemmatize_query
from app.search.mwe.idioms import _find_lemma_sequence
from app.search.mwe.lexicon import get_phrasal_verbs
from app.search.mwe.phrasal_verbs import _find_phrasal_verb_positions


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "_", text.strip().lower()).strip("_")


def _read_slice(
    source_csv: Path,
    start: int,
    end: int,
    speaker_col: str,
    line_col: str,
    season_col: str,
) -> list[dict]:
    rows = []
    with source_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i < start:
                continue
            if i > end:
                break
            rows.append({
                "line_index": i,
                "season": row.get(season_col, ""),
                "speaker": row.get(speaker_col, ""),
                "line": row.get(line_col, ""),
            })
    return rows


def _read_gold(gold_csv: Path) -> list[dict]:
    with gold_csv.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_predictions(pred_csv: Path, rows: list[dict]) -> None:
    pred_csv.parent.mkdir(parents=True, exist_ok=True)
    with pred_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "episode_name",
                "season",
                "line_index",
                "speaker",
                "line",
                "expression",
                "expression_type",
                "detector",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def _compute_metrics(gold_rows: list[dict], pred_rows: list[dict]) -> dict:
    gold_set = {
        (int(r["line_index"]), r["expression_type"], r["expression"]) for r in gold_rows
    }
    pred_set = {
        (int(r["line_index"]), r["expression_type"], r["expression"]) for r in pred_rows
    }
    tp = gold_set & pred_set
    fp = pred_set - gold_set
    fn = gold_set - pred_set
    precision = len(tp) / len(pred_set) if pred_set else 0.0
    recall = len(tp) / len(gold_set) if gold_set else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "gold_set": gold_set,
        "pred_set": pred_set,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _compute_type_metrics(gold_set: set, pred_set: set, expr_type: str) -> dict:
    g = {x for x in gold_set if x[1] == expr_type}
    p = {x for x in pred_set if x[1] == expr_type}
    tp = g & p
    fp = p - g
    fn = g - p
    precision = len(tp) / len(p) if p else 0.0
    recall = len(tp) / len(g) if g else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "gold": len(g),
        "pred": len(p),
        "tp": len(tp),
        "fp": len(fp),
        "fn": len(fn),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _format_items(items: set[tuple], line_map: dict[int, str], limit: int = 20) -> str:
    out = []
    for line_index, expr_type, expr in sorted(items)[:limit]:
        out.append(
            f"- line {line_index} | {expr_type} | `{expr}` | {line_map.get(line_index, '')}"
        )
    return "\n".join(out) if out else "- None"


def _write_report(
    report_path: Path,
    run_id: str,
    run_ts_iso: str,
    source_csv: Path,
    episode_name: str,
    start: int,
    end: int,
    gold_csv: Path,
    pred_csv: Path,
    metrics: dict,
    pv_metrics: dict,
    idiom_metrics: dict,
    line_map: dict[int, str],
) -> None:
    text = f"""# MWE Evaluation Report

## Run Metadata
- Run ID: `{run_id}`
- Generated at (UTC): `{run_ts_iso}`

## Dataset Scope
- Source file: `{source_csv.as_posix()}`
- Evaluated slice: `{episode_name}` (contiguous proxy episode)
- Slice definition: `line_index` {start}-{end} ({end - start + 1} dialogue lines)

## Files
- Gold annotations: `{gold_csv.as_posix()}`
- Engine predictions: `{pred_csv.as_posix()}`

## Overall Metrics
- Gold instances: {len(metrics["gold_set"])}
- Predicted instances: {len(metrics["pred_set"])}
- True Positives (TP): {len(metrics["tp"])}
- False Positives (FP): {len(metrics["fp"])}
- False Negatives (FN): {len(metrics["fn"])}
- Precision: {metrics["precision"]:.4f}
- Recall: {metrics["recall"]:.4f}
- F1 score: {metrics["f1"]:.4f}

## By Expression Type
### Phrasal Verbs
- Gold: {pv_metrics["gold"]}
- Predicted: {pv_metrics["pred"]}
- TP: {pv_metrics["tp"]}
- FP: {pv_metrics["fp"]}
- FN: {pv_metrics["fn"]}
- Precision: {pv_metrics["precision"]:.4f}
- Recall: {pv_metrics["recall"]:.4f}
- F1: {pv_metrics["f1"]:.4f}

### Idioms
- Gold: {idiom_metrics["gold"]}
- Predicted: {idiom_metrics["pred"]}
- TP: {idiom_metrics["tp"]}
- FP: {idiom_metrics["fp"]}
- FN: {idiom_metrics["fn"]}
- Precision: {idiom_metrics["precision"]:.4f}
- Recall: {idiom_metrics["recall"]:.4f}
- F1: {idiom_metrics["f1"]:.4f}

## Example False Positives (up to 20)
{_format_items(metrics["fp"], line_map)}

## Example False Negatives (up to 20)
{_format_items(metrics["fn"], line_map)}
"""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(text, encoding="utf-8")


def _write_metrics_json(path: Path, run_id: str, run_ts_iso: str, metrics: dict) -> None:
    payload = {
        "run_id": run_id,
        "generated_at_utc": run_ts_iso,
        "gold": len(metrics["gold_set"]),
        "predicted": len(metrics["pred_set"]),
        "tp": len(metrics["tp"]),
        "fp": len(metrics["fp"]),
        "fn": len(metrics["fn"]),
        "precision": round(metrics["precision"], 6),
        "recall": round(metrics["recall"], 6),
        "f1": round(metrics["f1"], 6),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _append_run_history(path: Path, run_row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        fieldnames = [
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
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(run_row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MWE evaluation against manual gold.")
    parser.add_argument("--config", default="manual_tests/manual_test_config.json")
    parser.add_argument("--dataset-id", default="")
    parser.add_argument("--split-id", default="")
    parser.add_argument("--output-root", default="")
    parser.add_argument("--source-csv", default="")
    parser.add_argument(
        "--gold-csv",
        default="",
        help="Optional explicit gold CSV path. If omitted, uses structured default.",
    )
    parser.add_argument("--start-line", type=int, default=None)
    parser.add_argument("--end-line", type=int, default=None)
    parser.add_argument("--speaker-col", default="")
    parser.add_argument("--line-col", default="")
    parser.add_argument("--season-col", default="")
    parser.add_argument(
        "--run-label",
        default="",
        help="Optional label appended to run id, e.g. 'after_gap_fix'.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    config = {}
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))

    def cfg(name: str, default):
        value = getattr(args, name)
        if value not in ("", None):
            return value
        return config.get(name, default)

    output_root = Path(cfg("output_root", "manual_tests"))
    dataset_id = _slug(cfg("dataset_id", "gilmore_girls"))
    split_id = _slug(cfg("split_id", "s01e01_proxy_l0000_0220"))
    case_dir = output_root / "datasets" / dataset_id / split_id
    runs_dir = case_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    source_csv = Path(cfg("source_csv", "data/Gilmore_Girls_Lines.csv"))
    if not source_csv.exists():
        raise FileNotFoundError(f"Source CSV not found: {source_csv}")

    if args.gold_csv:
        gold_csv = Path(args.gold_csv)
    else:
        gold_csv = case_dir / "gold.csv"
        if not gold_csv.exists():
            legacy = output_root / f"{split_id}_gold.csv"
            if legacy.exists():
                gold_csv = legacy
    if not gold_csv.exists():
        raise FileNotFoundError(
            "Gold CSV not found. Provide --gold-csv or place file at "
            f"{case_dir / 'gold.csv'}"
        )

    run_ts = datetime.now(timezone.utc)
    run_id = run_ts.strftime("%Y%m%d_%H%M%S")
    if args.run_label:
        run_id = f"{run_id}_{_slug(args.run_label)}"
    run_ts_iso = run_ts.isoformat()

    pred_csv = runs_dir / f"{run_id}_predictions.csv"
    report_md = runs_dir / f"{run_id}_report.md"
    metrics_json = runs_dir / f"{run_id}_metrics.json"

    rows = _read_slice(
        source_csv,
        cfg("start_line", 0),
        cfg("end_line", 220),
        cfg("speaker_col", "Character"),
        cfg("line_col", "Line"),
        cfg("season_col", "Season"),
    )
    line_map = {r["line_index"]: r["line"] for r in rows}
    gold_rows = _read_gold(gold_csv)
    episode_name = split_id

    nlp = get_nlp()
    for row in rows:
        doc = nlp(row["line"])
        row["lemmas"] = [t.lemma_.lower() for t in doc if not t.is_space and not t.is_punct]

    pvs = get_phrasal_verbs()
    pv_by_verb = defaultdict(list)
    for canonical, pv in pvs.items():
        search_lemmas = pv.get("search_lemmas")
        if not search_lemmas:
            particle_tokens = (pv.get("particle") or "").split()
            if particle_tokens and pv.get("verb_lemma"):
                search_lemmas = [pv["verb_lemma"]] + particle_tokens
        if not search_lemmas or len(search_lemmas) < 2:
            continue
        max_gap = 6 if pv.get("separable") else 3
        pv_by_verb[pv["verb_lemma"]].append((canonical, search_lemmas, max_gap))

    pred_rows = []
    for row in rows:
        lemmas = row["lemmas"]
        seen = set()
        for lemma in set(lemmas):
            for canonical, query_lemmas, max_gap in pv_by_verb.get(lemma, []):
                positions = _find_phrasal_verb_positions(lemmas, query_lemmas, max_gap=max_gap)
                if not positions:
                    continue
                key = ("phrasal_verb", canonical)
                if key in seen:
                    continue
                seen.add(key)
                pred_rows.append({
                    "episode_name": episode_name,
                    "season": row["season"],
                    "line_index": row["line_index"],
                    "speaker": row["speaker"],
                    "line": row["line"],
                    "expression": canonical,
                    "expression_type": "phrasal_verb",
                    "detector": "engine_phrasal_verb",
                })

    idiom_candidates = sorted({
        r["expression"] for r in gold_rows if r["expression_type"] == "idiom"
    })
    for row in rows:
        lemmas = row["lemmas"]
        for expr in idiom_candidates:
            query_lemmas = lemmatize_query(expr)
            if _find_lemma_sequence(lemmas, query_lemmas):
                pred_rows.append({
                    "episode_name": episode_name,
                    "season": row["season"],
                    "line_index": row["line_index"],
                    "speaker": row["speaker"],
                    "line": row["line"],
                    "expression": expr,
                    "expression_type": "idiom",
                    "detector": "engine_idiom",
                })

    unique = []
    seen = set()
    for row in pred_rows:
        key = (row["line_index"], row["expression_type"], row["expression"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)

    _write_predictions(pred_csv, unique)
    metrics = _compute_metrics(gold_rows, unique)
    pv_metrics = _compute_type_metrics(metrics["gold_set"], metrics["pred_set"], "phrasal_verb")
    idiom_metrics = _compute_type_metrics(metrics["gold_set"], metrics["pred_set"], "idiom")
    _write_report(
        report_md,
        run_id,
        run_ts_iso,
        source_csv,
        episode_name,
        cfg("start_line", 0),
        cfg("end_line", 220),
        gold_csv,
        pred_csv,
        metrics,
        pv_metrics,
        idiom_metrics,
        line_map,
    )
    _write_metrics_json(metrics_json, run_id, run_ts_iso, metrics)

    latest_pred = case_dir / "latest_predictions.csv"
    latest_report = case_dir / "latest_report.md"
    latest_metrics = case_dir / "latest_metrics.json"
    shutil.copy2(pred_csv, latest_pred)
    shutil.copy2(report_md, latest_report)
    shutil.copy2(metrics_json, latest_metrics)

    _append_run_history(
        case_dir / "run_history.csv",
        {
            "run_id": run_id,
            "generated_at_utc": run_ts_iso,
            "dataset_id": dataset_id,
            "split_id": split_id,
            "gold": len(metrics["gold_set"]),
            "predicted": len(metrics["pred_set"]),
            "tp": len(metrics["tp"]),
            "fp": len(metrics["fp"]),
            "fn": len(metrics["fn"]),
            "precision": f"{metrics['precision']:.6f}",
            "recall": f"{metrics['recall']:.6f}",
            "f1": f"{metrics['f1']:.6f}",
            "predictions_csv": pred_csv.as_posix(),
            "report_md": report_md.as_posix(),
            "metrics_json": metrics_json.as_posix(),
        },
    )

    print(f"Run ID: {run_id}")
    print(f"Predictions: {pred_csv}")
    print(f"Report: {report_md}")
    print(f"Metrics JSON: {metrics_json}")
    print(f"Latest report: {latest_report}")
    print(
        "Metrics:",
        {
            "gold": len(metrics["gold_set"]),
            "pred": len(metrics["pred_set"]),
            "tp": len(metrics["tp"]),
            "fp": len(metrics["fp"]),
            "fn": len(metrics["fn"]),
            "precision": round(metrics["precision"], 4),
            "recall": round(metrics["recall"], 4),
            "f1": round(metrics["f1"], 4),
        },
    )


if __name__ == "__main__":
    main()

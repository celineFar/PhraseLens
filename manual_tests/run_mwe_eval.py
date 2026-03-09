#!/usr/bin/env python3
"""Run MWE evaluation against manual gold with organized run outputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import mlflow
except ImportError:  # pragma: no cover - optional dependency in runtime
    mlflow = None

try:
    import tomllib
except ImportError:  # pragma: no cover - Python < 3.11
    tomllib = None

from app.nlp.pipeline import get_nlp, lemmatize_query
from app.search.mwe.idioms import _find_lemma_sequence
from app.search.mwe.lexicon import get_phrasal_verbs
from app.search.mwe.phrasal_verbs import _find_phrasal_verb_positions, PV_FILTERS


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


def _rows_from_gold(gold_rows: list[dict]) -> list[dict]:
    required = {"line_index", "season", "speaker", "line"}
    if not gold_rows:
        return []
    missing = required - set(gold_rows[0].keys())
    if missing:
        missing_str = ", ".join(sorted(missing))
        raise ValueError(
            "gold_only mode requires columns in gold CSV: "
            f"line_index, season, speaker, line. Missing: {missing_str}"
        )
    by_index: dict[int, dict] = {}
    for row in gold_rows:
        idx = int(row["line_index"])
        if idx not in by_index:
            by_index[idx] = {
                "line_index": idx,
                "season": row.get("season", ""),
                "speaker": row.get("speaker", ""),
                "line": row.get("line", ""),
            }
    return [by_index[i] for i in sorted(by_index)]


def _normalize_expression(expr: str) -> str:
    return expr.strip().lower()


def _match_key(row: dict, ignore_type: bool) -> tuple:
    line_index = int(row["line_index"])
    expr = _normalize_expression(row["expression"])
    if ignore_type:
        return (line_index, expr)
    return (line_index, row["expression_type"], expr)


def _build_comparison_rows(
    gold_rows: list[dict],
    pred_rows: list[dict],
    ignore_type: bool = False,
) -> list[dict]:
    pred_by_key = {_match_key(r, ignore_type): r for r in pred_rows}
    gold_by_key = {_match_key(r, ignore_type): r for r in gold_rows}

    rows: list[dict] = []

    for gr in gold_rows:
        key = _match_key(gr, ignore_type)
        pred = pred_by_key.get(key)
        out = dict(gr)
        out["predicted"] = "yes" if pred else "no"
        out["prediction_expression"] = pred["expression"] if pred else ""
        out["prediction_type"] = pred["expression_type"] if pred else ""
        out["prediction_detector"] = pred["detector"] if pred else ""
        out["match_status"] = "tp" if pred else "fn"
        rows.append(out)

    for key, pr in pred_by_key.items():
        if key in gold_by_key:
            continue
        rows.append({
            "episode_name": pr["episode_name"],
            "season": pr["season"],
            "line_index": pr["line_index"],
            "speaker": pr["speaker"],
            "line": pr["line"],
            "expression": "",
            "expression_type": "",
            "label": "",
            "notes": "",
            "predicted": "yes",
            "prediction_expression": pr["expression"],
            "prediction_type": pr["expression_type"],
            "prediction_detector": pr["detector"],
            "match_status": "fp",
        })

    rows.sort(
        key=lambda r: (
            int(r.get("line_index", 0)),
            r.get("expression_type", ""),
            r.get("expression", ""),
            r.get("prediction_type", ""),
            r.get("prediction_expression", ""),
        )
    )
    return rows


def _write_predictions(pred_csv: Path, rows: list[dict], gold_rows: list[dict]) -> None:
    pred_csv.parent.mkdir(parents=True, exist_ok=True)
    gold_fields = list(gold_rows[0].keys()) if gold_rows else [
        "episode_name",
        "season",
        "line_index",
        "speaker",
        "line",
        "expression",
        "expression_type",
        "label",
        "notes",
    ]
    extra_fields = [
        "predicted",
        "prediction_expression",
        "prediction_type",
        "prediction_detector",
        "match_status",
    ]
    with pred_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=gold_fields + extra_fields)
        writer.writeheader()
        writer.writerows(rows)


def _compute_metrics(gold_rows: list[dict], pred_rows: list[dict], ignore_type: bool = False) -> dict:
    gold_set = {_match_key(r, ignore_type) for r in gold_rows}
    pred_set = {_match_key(r, ignore_type) for r in pred_rows}
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
    for item in sorted(items)[:limit]:
        if len(item) == 3:
            line_index, expr_type, expr = item
        else:
            line_index, expr = item
            expr_type = "*"
        out.append(
            f"- line {line_index} | {expr_type} | `{expr}` | {line_map.get(line_index, '')}"
        )
    return "\n".join(out) if out else "- None"


def _write_report(
    report_path: Path,
    run_id: str,
    run_ts_iso: str,
    source_desc: str,
    episode_name: str,
    start: int | None,
    end: int | None,
    evaluated_line_count: int,
    gold_csv: Path,
    pred_csv: Path,
    metrics: dict,
    pv_metrics: dict,
    idiom_metrics: dict,
    line_map: dict[int, str],
    match_mode: str,
    run_notes: str,
) -> None:
    text = f"""# MWE Evaluation Report

## Run Metadata
- Run ID: `{run_id}`
- Generated at (UTC): `{run_ts_iso}`
- Run notes: `{run_notes if run_notes else "-"}` 

## Dataset Scope
- Source: `{source_desc}`
- Evaluated slice: `{episode_name}` (contiguous proxy episode)
- Slice definition: `line_index` {start}-{end} ({(end - start + 1) if (start is not None and end is not None) else "N/A"} dialogue lines)
- Prediction input lines: {evaluated_line_count} gold-covered lines only
- Match mode: `{match_mode}` (`ignore_type` treats same expression text as correct even with different expression_type)

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
    base_fieldnames = [
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
    extended_fieldnames = base_fieldnames + ["run_notes"]
    write_header = not path.exists()
    fieldnames = extended_fieldnames
    if path.exists():
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, [])
        if header:
            if "run_notes" in header:
                fieldnames = extended_fieldnames
            else:
                fieldnames = base_fieldnames
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        filtered_row = {k: run_row.get(k, "") for k in fieldnames}
        writer.writerow(filtered_row)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_git_command(args: list[str]) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return False, ""
    if proc.returncode != 0:
        return False, ""
    return True, proc.stdout.strip()


def _collect_git_run_metadata(runs_dir: Path, run_id: str) -> tuple[dict, dict, list[Path]]:
    params: dict[str, str] = {}
    tags: dict[str, str] = {}
    artifacts: list[Path] = []

    ok, commit = _run_git_command(["rev-parse", "HEAD"])
    if ok and commit:
        params["git_commit"] = commit
        tags["git_commit"] = commit

    ok, short_commit = _run_git_command(["rev-parse", "--short", "HEAD"])
    if ok and short_commit:
        params["git_commit_short"] = short_commit

    ok, branch = _run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    if ok and branch:
        params["git_branch"] = branch
        tags["git_branch"] = branch

    ok, status_porcelain = _run_git_command(["status", "--porcelain"])
    if ok:
        git_dirty = bool(status_porcelain)
        params["git_dirty"] = str(git_dirty).lower()
        tags["git_dirty"] = str(git_dirty).lower()

    ok, status_short = _run_git_command(["status", "--short", "--branch"])
    if ok and status_short:
        status_path = runs_dir / f"{run_id}_git_status.txt"
        status_path.write_text(status_short + "\n", encoding="utf-8")
        artifacts.append(status_path)

    if params.get("git_dirty") == "true":
        ok, diff = _run_git_command(["diff", "--no-ext-diff", "HEAD"])
        if ok and diff:
            diff_path = runs_dir / f"{run_id}_git_diff.patch"
            diff_path.write_text(diff, encoding="utf-8")
            artifacts.append(diff_path)

    return params, tags, artifacts


def _log_mlflow_run(
    enabled: bool,
    tracking_uri: str,
    experiment: str,
    run_name: str,
    params: dict,
    metrics: dict,
    artifacts: list[Path],
    tags: dict,
) -> None:
    if not enabled:
        return
    if mlflow is None:
        raise RuntimeError(
            "MLflow logging is enabled but mlflow is not installed. "
            "Install dependencies from requirements.txt first."
        )

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment)
    with mlflow.start_run(run_name=run_name):
        mlflow.set_tags({k: str(v) for k, v in tags.items()})
        mlflow.log_params({k: str(v) for k, v in params.items()})
        mlflow.log_metrics(metrics)
        for path in artifacts:
            if path.exists():
                mlflow.log_artifact(path.as_posix())


def _load_config(config_path: Path) -> dict:
    if not config_path.exists():
        return {}

    suffix = config_path.suffix.lower()
    if suffix == ".json":
        return json.loads(config_path.read_text(encoding="utf-8"))
    if suffix == ".toml":
        if tomllib is None:
            raise RuntimeError(
                "TOML config requested but tomllib is unavailable in this Python runtime."
            )
        with config_path.open("rb") as f:
            return tomllib.load(f)
    raise ValueError("Unsupported config format. Use .toml or .json")


def _version_key_from_gold_filename(path: Path) -> tuple:
    stem = path.stem.lower()
    if not stem.startswith("gold_v"):
        return (0, [], path.name.lower())
    suffix = stem[len("gold_v") :]
    nums = [int(x) for x in re.findall(r"\d+", suffix)]
    return (1, nums, path.name.lower())


def _resolve_gold_csv(case_dir: Path, configured_gold_csv: str, output_root: Path) -> Path:
    if configured_gold_csv:
        gold_csv = Path(configured_gold_csv)
    else:
        gold_csv = case_dir / "gold.csv"
    if gold_csv.exists():
        return gold_csv

    if not configured_gold_csv:
        legacy = output_root / f"{case_dir.name}_gold.csv"
        if legacy.exists():
            return legacy

    versioned = sorted(case_dir.glob("gold_v*.csv"), key=_version_key_from_gold_filename)
    if versioned:
        return versioned[-1]

    return gold_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MWE evaluation against manual gold.")
    parser.add_argument("--config", default="manual_tests/manual_test_config.toml")
    parser.add_argument("--dataset-id", default="")
    parser.add_argument("--split-id", default="")
    parser.add_argument("--output-root", default="")
    parser.add_argument("--source-csv", default="")
    parser.add_argument(
        "--input-mode",
        default="",
        help="Use full transcript slice ('transcript') or use gold.csv lines directly ('gold_only').",
    )
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
    parser.add_argument(
        "--run-notes",
        default="",
        help="Optional free-text notes for this run (logged to report/history/MLflow).",
    )
    parser.add_argument(
        "--pv-filter",
        default="",
        help="Phrasal verb filter strategy: " + ", ".join(PV_FILTERS.keys()),
    )
    parser.add_argument(
        "--match-mode",
        default="",
        help="Evaluation matching mode: strict or ignore_type",
    )
    parser.add_argument(
        "--mlflow-mode",
        default="",
        help="MLflow logging mode: enabled or disabled",
    )
    parser.add_argument(
        "--mlflow-tracking-uri",
        default="",
        help="MLflow tracking URI (default: file:<output_root>/mlruns)",
    )
    parser.add_argument(
        "--mlflow-experiment",
        default="",
        help="MLflow experiment name",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    config = _load_config(config_path)

    def cfg(name: str, default):
        value = getattr(args, name)
        if value not in ("", None):
            return value
        cfg_value = config.get(name, default)
        if cfg_value in ("", None):
            return default
        return cfg_value

    output_root = Path(cfg("output_root", "manual_tests"))
    dataset_id = _slug(cfg("dataset_id", "gilmore_girls"))
    split_id = _slug(cfg("split_id", "s01e01_proxy_l0000_0220"))
    input_mode = cfg("input_mode", "transcript")
    if input_mode not in ("transcript", "gold_only"):
        raise ValueError("Invalid input_mode. Valid values: transcript, gold_only")
    pv_filter = cfg("pv_filter", "none")
    if pv_filter not in PV_FILTERS:
        raise ValueError(
            f"Invalid pv_filter: {pv_filter}. Valid values: {', '.join(PV_FILTERS.keys())}"
        )
    match_mode = cfg("match_mode", "strict")
    if match_mode not in ("strict", "ignore_type"):
        raise ValueError("Invalid match_mode. Valid values: strict, ignore_type")
    ignore_type = match_mode == "ignore_type"
    mlflow_mode = cfg("mlflow_mode", "auto")
    if mlflow_mode not in ("auto", "enabled", "disabled"):
        raise ValueError("Invalid mlflow_mode. Valid values: auto, enabled, disabled")
    if mlflow_mode == "enabled":
        mlflow_enabled = True
    elif mlflow_mode == "disabled":
        mlflow_enabled = False
    else:
        mlflow_enabled = mlflow is not None
        if not mlflow_enabled:
            print("MLflow disabled (auto mode): mlflow package is not installed.")
    case_dir = output_root / "datasets" / dataset_id / split_id
    runs_dir = case_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    mlflow_tracking_uri = cfg(
        "mlflow_tracking_uri",
        f"file:{(output_root / 'mlruns').resolve().as_posix()}",
    )
    mlflow_experiment = cfg("mlflow_experiment", "manual_tests")

    configured_gold_csv = cfg("gold_csv", "")
    gold_csv = _resolve_gold_csv(case_dir, configured_gold_csv, output_root)
    if not gold_csv.exists():
        raise FileNotFoundError(
            "Gold CSV not found. Provide --gold-csv or place file at "
            f"{case_dir / 'gold.csv'} (or a versioned file like gold_v1.csv)"
        )

    source_desc = f"{gold_csv.as_posix()} (gold_only)"
    start = None
    end = None

    run_ts = datetime.now(timezone.utc)
    run_id = run_ts.strftime("%Y%m%d_%H%M%S")
    run_label = cfg("run_label", "")
    run_notes = cfg("run_notes", "").strip()
    if run_label:
        run_id = f"{run_id}_{_slug(run_label)}"
    run_ts_iso = run_ts.isoformat()

    pred_csv = runs_dir / f"{run_id}_predictions.csv"
    report_md = runs_dir / f"{run_id}_report.md"
    metrics_json = runs_dir / f"{run_id}_metrics.json"
    notes_txt = runs_dir / f"{run_id}_notes.txt"
    if run_notes:
        notes_txt.write_text(run_notes + "\n", encoding="utf-8")

    gold_rows = _read_gold(gold_csv)
    if input_mode == "gold_only":
        rows = _rows_from_gold(gold_rows)
        if rows:
            start = min(r["line_index"] for r in rows)
            end = max(r["line_index"] for r in rows)
    else:
        source_csv = Path(cfg("source_csv", "data/Gilmore_Girls_Lines.csv"))
        if not source_csv.exists():
            raise FileNotFoundError(f"Source CSV not found: {source_csv}")
        start = cfg("start_line", 0)
        end = cfg("end_line", 220)
        rows = _read_slice(
            source_csv,
            start,
            end,
            cfg("speaker_col", "Character"),
            cfg("line_col", "Line"),
            cfg("season_col", "Season"),
        )
        source_desc = source_csv.as_posix()

    gold_line_indices = {int(r["line_index"]) for r in gold_rows}
    slice_line_indices = {r["line_index"] for r in rows}
    missing_gold_lines = sorted(gold_line_indices - slice_line_indices)
    if missing_gold_lines:
        missing_preview = ", ".join(str(i) for i in missing_gold_lines[:10])
        raise ValueError(
            "Gold CSV contains line_index values outside the configured slice: "
            f"{missing_preview}"
            + ("..." if len(missing_gold_lines) > 10 else "")
        )
    rows = [r for r in rows if r["line_index"] in gold_line_indices]
    line_map = {r["line_index"]: r["line"] for r in rows}
    episode_name = split_id

    nlp = get_nlp()
    for row in rows:
        doc = nlp(row["line"])
        row["doc"] = doc
        row["lemmas"] = [t.lemma_.lower() for t in doc if not t.is_space and not t.is_punct]

    pvs = get_phrasal_verbs()
    # TODO: deos this read all the phrasal verbs? shouldn't it be a db lookup? indexed?
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

    pv_filter_fn = PV_FILTERS[pv_filter]
    pred_rows = []
    for row in rows:
        lemmas = row["lemmas"]
        doc = row["doc"]
        seen = set()
        for lemma in set(lemmas):
            for canonical, query_lemmas, max_gap in pv_by_verb.get(lemma, []):
                positions = _find_phrasal_verb_positions(lemmas, query_lemmas, max_gap=max_gap)
                if not positions:
                    continue
                verb_lemma = query_lemmas[0]
                particle_lemmas = query_lemmas[1:]
                if not pv_filter_fn(doc, verb_lemma, particle_lemmas):
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

    comparison_rows = _build_comparison_rows(gold_rows, unique, ignore_type=ignore_type)
    _write_predictions(pred_csv, comparison_rows, gold_rows)
    metrics = _compute_metrics(gold_rows, unique, ignore_type=ignore_type)
    strict_metrics = _compute_metrics(gold_rows, unique, ignore_type=False)
    pv_metrics = _compute_type_metrics(
        strict_metrics["gold_set"], strict_metrics["pred_set"], "phrasal_verb"
    )
    idiom_metrics = _compute_type_metrics(
        strict_metrics["gold_set"], strict_metrics["pred_set"], "idiom"
    )
    _write_report(
        report_md,
        run_id,
        run_ts_iso,
        source_desc,
        episode_name,
        start,
        end,
        len(rows),
        gold_csv,
        pred_csv,
        metrics,
        pv_metrics,
        idiom_metrics,
        line_map,
        match_mode,
        run_notes,
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
            "run_notes": run_notes,
        },
    )

    git_params, git_tags, git_artifacts = _collect_git_run_metadata(runs_dir, run_id)

    _log_mlflow_run(
        enabled=mlflow_enabled,
        tracking_uri=mlflow_tracking_uri,
        experiment=mlflow_experiment,
        run_name=run_id,
        params={
            "dataset_id": dataset_id,
            "split_id": split_id,
            "input_mode": input_mode,
            "pv_filter": pv_filter,
            "match_mode": match_mode,
            "run_label": run_label,
            "run_notes": run_notes,
            "mlflow_mode": mlflow_mode,
            "source_desc": source_desc,
            "gold_csv": gold_csv.as_posix(),
            "gold_sha256": _sha256_file(gold_csv),
            "gold_rows": len(gold_rows),
            "config_path": config_path.as_posix(),
            **git_params,
        },
        metrics={
            "gold": float(len(metrics["gold_set"])),
            "predicted": float(len(metrics["pred_set"])),
            "tp": float(len(metrics["tp"])),
            "fp": float(len(metrics["fp"])),
            "fn": float(len(metrics["fn"])),
            "precision": float(metrics["precision"]),
            "recall": float(metrics["recall"]),
            "f1": float(metrics["f1"]),
            "pv_precision_strict": float(pv_metrics["precision"]),
            "pv_recall_strict": float(pv_metrics["recall"]),
            "pv_f1_strict": float(pv_metrics["f1"]),
            "idiom_precision_strict": float(idiom_metrics["precision"]),
            "idiom_recall_strict": float(idiom_metrics["recall"]),
            "idiom_f1_strict": float(idiom_metrics["f1"]),
        },
        artifacts=[
            config_path,
            gold_csv,
            pred_csv,
            report_md,
            metrics_json,
            notes_txt,
            latest_pred,
            latest_report,
            latest_metrics,
            case_dir / "run_history.csv",
            *git_artifacts,
        ],
        tags={
            "component": "manual_tests",
            "dataset": dataset_id,
            "split": split_id,
            "run_id": run_id,
            "generated_at_utc": run_ts_iso,
            "run_notes": run_notes,
            **git_tags,
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

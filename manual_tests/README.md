# Manual MWE Tests

## Structure

```
manual_tests/
  run_mwe_eval.py
  datasets/
    <dataset_id>/
      <split_id>/
        gold.csv
        latest_predictions.csv
        latest_report.md
        latest_metrics.json
        run_history.csv
        runs/
          <timestamp>[_label]_predictions.csv
          <timestamp>[_label]_report.md
          <timestamp>[_label]_metrics.json
```

## Default Run

```bash
.venv/bin/python manual_tests/run_mwe_eval.py
```

This uses defaults from `manual_tests/manual_test_config.json`.

## Common Options

- `--dataset-id gilmore_girls`
- `--split-id s01e01_proxy_l0000_0220`
- `--input-mode transcript|gold_only`
- `--match-mode strict|ignore_type`
- `--source-csv data/Gilmore_Girls_Lines.csv`
- `--start-line 0 --end-line 220`
- `--run-label after_gap_fix`
- `--pv-filter dep_extended`

Example:

```bash
.venv/bin/python manual_tests/run_mwe_eval.py \
  --dataset-id gilmore_girls \
  --split-id s01e01_proxy_l0000_0220 \
  --run-label trial_1
```

Gold-only mode example (use annotated rows in `gold.csv` as evaluation input):

```bash
.venv/bin/python manual_tests/run_mwe_eval.py \
  --dataset-id himym \
  --split-id s04e12_benefits_l1055_1259 \
  --input-mode gold_only \
  --gold-csv manual_tests/datasets/himym/s04e12_benefits_l1055_1259/gold.csv \
  --match-mode ignore_type \
  --pv-filter dep_extended
```

## Add Another Dataset/Split

1. Create: `manual_tests/datasets/<dataset_id>/<split_id>/`
2. Put your manual gold file as: `gold.csv`
3. Run `run_mwe_eval.py` with matching `--dataset-id`, `--split-id`, and `--source-csv`.

For non-Gilmore CSV schemas, set:
- `--speaker-col`
- `--line-col`
- `--season-col`

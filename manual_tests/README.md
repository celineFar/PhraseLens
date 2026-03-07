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
- `--source-csv data/Gilmore_Girls_Lines.csv`
- `--start-line 0 --end-line 220`
- `--run-label after_gap_fix`

Example:

```bash
.venv/bin/python manual_tests/run_mwe_eval.py \
  --dataset-id gilmore_girls \
  --split-id s01e01_proxy_l0000_0220 \
  --run-label trial_1
```

## Add Another Dataset/Split

1. Create: `manual_tests/datasets/<dataset_id>/<split_id>/`
2. Put your manual gold file as: `gold.csv`
3. Run `run_mwe_eval.py` with matching `--dataset-id`, `--split-id`, and `--source-csv`.

For non-Gilmore CSV schemas, set:
- `--speaker-col`
- `--line-col`
- `--season-col`

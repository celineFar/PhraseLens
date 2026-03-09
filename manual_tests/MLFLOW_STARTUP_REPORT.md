# MLflow Startup Report (Manual Tests)

This report documents the repeatable steps to start MLflow for manual test runs in this repo.

## Purpose

- Track manual test runs from `manual_tests/run_mwe_eval.py`.
- View runs, params, metrics, and artifacts in the MLflow UI.

## One-Time Setup

Run these from the repo root:

```bash
cd /home/ubuntu/PhraseLens
.venv/bin/pip install -r requirements.txt
```

## Start MLflow Each Time

Run this each time you want the UI available:

```bash
cd /home/ubuntu/PhraseLens
.venv/bin/mlflow ui \
  --backend-store-uri file:/home/ubuntu/PhraseLens/manual_tests/mlruns \
  --host 0.0.0.0 \
  --port 5000
```

Then open:

- Local: `http://127.0.0.1:5000/`
- Remote host example: `http://18.234.75.185:5000/`

## Run From `.venv` (Activated Environment)

If you prefer activating the environment first:

```bash
cd /home/ubuntu/PhraseLens
source .venv/bin/activate
```

Then use regular commands:

```bash
pip install -r requirements.txt
mlflow ui \
  --backend-store-uri file:/home/ubuntu/PhraseLens/manual_tests/mlruns \
  --host 0.0.0.0 \
  --port 5000
```

## Optional: Background Start

```bash
cd /home/ubuntu/PhraseLens
nohup .venv/bin/mlflow ui \
  --backend-store-uri file:/home/ubuntu/PhraseLens/manual_tests/mlruns \
  --host 0.0.0.0 \
  --port 5000 >/tmp/mlflow.log 2>&1 &
```

## Verify It Is Up

```bash
ss -ltnp | rg ':5000'
```

If needed, ensure inbound `TCP 5000` is allowed in your cloud/security group and host firewall.

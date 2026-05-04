# Kubeflow Fraud Detection Pipeline

This project compiles a Kubeflow Pipelines YAML for a simple fraud detection workflow:

1. Generate imbalanced sample data.
2. Preprocess the data.
3. Train a balanced random forest classifier.
4. Log accuracy, precision, recall, and F1 score.

## Compile

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python fraud_pipeline.py
```

The compiled pipeline is written to `fraud.yaml`.

## Upload to Kubeflow

Upload `fraud.yaml` in the Kubeflow Pipelines UI, or submit it from Python using your Kubeflow endpoint.

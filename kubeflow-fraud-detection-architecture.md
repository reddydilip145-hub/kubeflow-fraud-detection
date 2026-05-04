# Kubeflow Fraud Detection Pipeline Architecture

## Overview

This project implements a fraud detection machine learning workflow using Kubeflow Pipelines on Kubernetes.

The pipeline is written in Python using the KFP DSL, compiled into a YAML pipeline definition, uploaded into Kubeflow Pipelines, and executed as Kubernetes pods through Argo Workflows.

## Architecture Diagram

The architecture diagram is stored as a normal SVG image so it renders in README viewers that do not support Mermaid.

![Kubeflow fraud detection architecture](screenshots/architecture-diagram.svg)

Architecture diagram file:

```text
C:/Users/abcom/Documents/Codex/2026-05-02/i-want-have-fraud-detecrion-in/screenshots/architecture-diagram.svg
```

## High-Level Flow

```text
Developer -> fraud_pipeline_harder.py -> fraud_harder_split.yaml
Kubeflow UI -> ml-pipeline API -> Argo Workflow Controller
Argo -> load-data -> preprocess-data -> split-data -> train-model -> evaluate-model
Pipeline pods -> SeaweedFS artifact store + ML Metadata
evaluate-model -> Kubeflow metrics artifact
```

## Component Architecture

| Area | Components |
|---|---|
| Development | `fraud_pipeline_harder.py`, `fraud_harder_split.yaml` |
| Kubeflow Pipelines | `ml-pipeline-ui`, `ml-pipeline API`, `mysql`, `ml-pipeline-persistenceagent` |
| Argo Workflows | `workflow-controller`, `argoexec:v3.7.3-nonroot` |
| Pipeline runtime pods | `load-data`, `preprocess-data`, `split-data`, `train-model`, `evaluate-model` |
| Storage and metadata | `seaweedfs` / MinIO-compatible artifacts, `metadata-grpc`, `metadata-envoy` |

## Pipeline Flow

1. Developer uploads `fraud_harder_split.yaml` in the Kubeflow Pipelines UI.
2. `ml-pipeline` registers the pipeline and stores metadata in MySQL.
3. A one-off run creates an Argo Workflow.
4. Argo starts the root driver and then executes the pipeline pods in dependency order.
5. `load-data` creates the 50,000-row synthetic fraud dataset.
6. `preprocess-data` cleans the dataset.
7. `split-data` creates train and test artifacts.
8. `train-model` trains a `RandomForestClassifier` using only train data.
9. `evaluate-model` evaluates using only test data and writes metrics.
10. Kubeflow UI displays run status, graph, artifacts, and metrics.

## Pipeline Steps

| Step | Purpose | Output |
|---|---|---|
| `load-data` | Creates an imbalanced synthetic fraud-like dataset | Raw dataset artifact |
| `preprocess-data` | Reads dataset and removes missing values | Processed dataset artifact |
| `split-data` | Creates stratified train/test datasets | `train_data`, `test_data` |
| `train-model` | Trains a `RandomForestClassifier` | Model artifact |
| `evaluate-model` | Calculates metrics on test data only | Accuracy, precision, recall, F1 score, ROC AUC, row counts |

## Kubernetes / Kubeflow Components

| Component | Role |
|---|---|
| `ml-pipeline-ui` | Web UI for uploading pipelines, creating experiments, and starting runs |
| `ml-pipeline` | Backend API server for pipelines, experiments, and runs |
| `workflow-controller` | Argo controller that launches pipeline tasks as Kubernetes pods |
| `mysql` | Stores pipeline, run, and experiment metadata |
| `metadata-grpc` / `metadata-envoy` | ML Metadata service for lineage and artifact metadata |
| `seaweedfs` / `minio-service` | S3-compatible artifact storage |
| `pipeline-runner` | Service account used by pipeline run pods |

## Important Metrics

For fraud detection, accuracy alone can be misleading because fraud data is usually imbalanced.

The final hardened run logs:

| Metric | Meaning |
|---|---|
| `accuracy` | Overall correct predictions |
| `precision` | How many predicted fraud rows were truly fraud |
| `recall` | How many actual fraud rows were caught |
| `f1_score` | Balance between precision and recall |
| `roc_auc` | Ranking quality across thresholds |
| `test_rows` | Number of test rows used for evaluation |
| `test_fraud_rows` | Number of fraud rows in the test split |
| `mismatch_count` | Number of predictions that did not match test labels |

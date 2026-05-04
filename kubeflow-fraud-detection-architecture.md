# Kubeflow Fraud Detection Pipeline Architecture

## Overview

This project implements a fraud detection machine learning workflow using Kubeflow Pipelines on Kubernetes/GKE.

The pipeline is written in Python using the KFP DSL, compiled into a YAML pipeline definition, uploaded into Kubeflow Pipelines, and executed as Kubernetes pods through Argo Workflows.

## Architecture Diagram

```mermaid
flowchart TD
    A["Developer / GitHub Repo"] --> B["fraud_pipeline.py"]
    B --> C["Compiled Pipeline YAML<br/>fraud.yaml"]

    C --> D["Kubeflow Pipelines UI<br/>ml-pipeline-ui"]
    D --> E["Kubeflow Pipelines API<br/>ml-pipeline"]

    E --> F["Argo Workflow Controller"]
    F --> G["Pipeline Run Pods"]

    G --> H1["load-data<br/>Generate fraud-like dataset"]
    H1 --> H2["preprocess-data<br/>Clean dataset"]
    H2 --> H3["train-model<br/>RandomForestClassifier"]
    H3 --> H4["evaluate-model<br/>Accuracy / Precision / Recall / F1"]

    G --> I["SeaweedFS / MinIO-compatible<br/>Artifact Store"]
    E --> J["MySQL<br/>Pipeline metadata DB"]
    G --> K["ML Metadata<br/>metadata-grpc / metadata-envoy"]

    H4 --> L["Metrics in Kubeflow UI"]
```

## Component Diagram

```mermaid
flowchart LR
    subgraph UserSide["User Side"]
        U["User / Developer"]
        R["GitHub Repo"]
        Y["fraud.yaml"]
    end

    subgraph Kubeflow["Kubeflow Namespace"]
        UI["ml-pipeline-ui"]
        API["ml-pipeline API"]
        WF["workflow-controller"]
        DB["mysql"]
        MLMD["metadata-grpc / metadata-envoy"]
        STORE["seaweedfs / minio-service"]
    end

    subgraph Runtime["Pipeline Runtime Pods"]
        L["load-data"]
        P["preprocess-data"]
        T["train-model"]
        E["evaluate-model"]
    end

    U --> R
    R --> Y
    Y --> UI
    UI --> API
    API --> WF
    API --> DB
    WF --> L
    L --> P
    P --> T
    T --> E
    L --> STORE
    P --> STORE
    T --> STORE
    E --> STORE
    L --> MLMD
    P --> MLMD
    T --> MLMD
    E --> MLMD
```

## Pipeline Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant UI as Kubeflow Pipelines UI
    participant API as ml-pipeline API
    participant Argo as Argo Workflow Controller
    participant Pods as Pipeline Pods
    participant Store as SeaweedFS Artifact Store
    participant DB as MySQL / MLMD

    Dev->>UI: Upload fraud.yaml
    UI->>API: Register pipeline
    API->>DB: Store pipeline metadata
    Dev->>UI: Create experiment and run
    UI->>API: Create run request
    API->>Argo: Create workflow
    Argo->>Pods: Start load-data pod
    Pods->>Store: Save generated dataset
    Pods->>DB: Write execution metadata
    Argo->>Pods: Start preprocess-data pod
    Pods->>Store: Save processed dataset
    Argo->>Pods: Start train-model pod
    Pods->>Store: Save trained model
    Argo->>Pods: Start evaluate-model pod
    Pods->>DB: Log metrics
    UI->>API: Fetch run status and metrics
```

## Pipeline Steps

| Step | Purpose | Output |
|---|---|---|
| `load-data` | Creates an imbalanced synthetic fraud-like dataset | Raw dataset artifact |
| `preprocess-data` | Reads dataset and removes missing values | Processed dataset artifact |
| `train-model` | Trains a `RandomForestClassifier` | Model artifact |
| `evaluate-model` | Calculates metrics | Accuracy, precision, recall, F1 score |

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

## Runtime Flow

1. Developer writes `fraud_pipeline.py`.
2. Pipeline is compiled into `fraud.yaml`.
3. `fraud.yaml` is uploaded into Kubeflow Pipelines UI.
4. User creates an experiment.
5. User starts a one-off run.
6. `ml-pipeline` creates an Argo Workflow.
7. Argo launches one Kubernetes pod per pipeline step.
8. Artifacts are written to SeaweedFS.
9. Metadata is written to MySQL and MLMD.
10. Metrics are displayed in the Kubeflow Pipelines UI.

## Important Metrics

For fraud detection, accuracy alone can be misleading because fraud data is usually imbalanced.

The most useful metrics are:

- `precision`
- `recall`
- `f1_score`
- `accuracy`

Recall and F1 score are especially important when the goal is to catch rare fraud cases.


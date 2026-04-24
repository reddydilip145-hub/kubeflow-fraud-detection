from kfp import dsl, compiler
from kfp.dsl import component, Input, Output, Dataset, Model, Metrics
import os

print("🚀 Script started")
print("📁 Current working directory:", os.getcwd())

# -------------------------------
# 1. Load Data
# -------------------------------
@component(base_image="python:3.10")
def load_data(output_data: Output[Dataset]):
    import pandas as pd
    from sklearn.datasets import make_classification

    X, y = make_classification(n_samples=1000, weights=[0.95], random_state=42)
    df = pd.DataFrame(X)
    df['target'] = y
    df.to_csv(output_data.path, index=False)


# -------------------------------
# 2. Preprocess Data
# -------------------------------
@component(base_image="python:3.10")
def preprocess_data(input_data: Input[Dataset], processed_data: Output[Dataset]):
    import pandas as pd

    df = pd.read_csv(input_data.path)
    df = df.dropna()
    df.to_csv(processed_data.path, index=False)


# -------------------------------
# 3. Train Model
# -------------------------------
@component(base_image="python:3.10")
def train_model(processed_data: Input[Dataset], model: Output[Model]):
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    import joblib

    df = pd.read_csv(processed_data.path)

    X = df.drop('target', axis=1)
    y = df['target']

    clf = RandomForestClassifier()
    clf.fit(X, y)

    joblib.dump(clf, model.path)


# -------------------------------
# 4. Evaluate Model
# -------------------------------
@component(base_image="python:3.10")
def evaluate_model(processed_data: Input[Dataset], model: Input[Model], metrics: Output[Metrics]):
    import pandas as pd
    import joblib
    from sklearn.metrics import accuracy_score

    df = pd.read_csv(processed_data.path)

    X = df.drop('target', axis=1)
    y = df['target']

    clf = joblib.load(model.path)
    preds = clf.predict(X)

    acc = accuracy_score(y, preds)
    metrics.log_metric("accuracy", acc)


# -------------------------------
# 5. Pipeline Definition
# -------------------------------
@dsl.pipeline(name="fraud-detection-pipeline")
def pipeline():
    load_task = load_data()

    preprocess_task = preprocess_data(
        input_data=load_task.outputs["output_data"]
    )

    train_task = train_model(
        processed_data=preprocess_task.outputs["processed_data"]
    )

    evaluate_task = evaluate_model(
        processed_data=preprocess_task.outputs["processed_data"],
        model=train_task.outputs["model"]
    )


# -------------------------------
# 6. FORCE COMPILE + DEBUG
# -------------------------------
output_path = r"C:\Users\abcom\Desktop\kubeflow-fraud-detection\fraud_pipeline.yaml"

print("🛠 Compiling pipeline to:", output_path)

compiler.Compiler().compile(
    pipeline_func=pipeline,
    package_path=output_path
)

print("✅ Compilation finished")

# verify file creation
if os.path.exists(output_path):
    print("🎉 YAML CREATED SUCCESSFULLY")
else:
    print("❌ YAML NOT CREATED — CHECK ISSUE")

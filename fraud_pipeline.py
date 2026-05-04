from kfp import compiler, dsl
from kfp.dsl import Dataset, Input, Metrics, Model, Output, component


PYTHON_BASE_IMAGE = "python:3.10"
COMPONENT_PACKAGES = [
    "pandas==2.2.2",
    "scikit-learn==1.5.1",
    "joblib==1.4.2",
]


@component(base_image=PYTHON_BASE_IMAGE, packages_to_install=COMPONENT_PACKAGES)
def load_data(output_data: Output[Dataset]):
    import pandas as pd
    from sklearn.datasets import make_classification

    X, y = make_classification(
        n_samples=50000,
        n_features=30,
        n_informative=12,
        n_redundant=6,
        weights=[0.98, 0.02],
        class_sep=1.2,
        flip_y=0.01,
        random_state=42,
    )

    df = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(X.shape[1])])
    df["target"] = y
    df.to_csv(output_data.path, index=False)


@component(base_image=PYTHON_BASE_IMAGE, packages_to_install=COMPONENT_PACKAGES)
def preprocess_data(input_data: Input[Dataset], processed_data: Output[Dataset]):
    import pandas as pd

    df = pd.read_csv(input_data.path)
    df = df.dropna()
    df.to_csv(processed_data.path, index=False)


@component(base_image=PYTHON_BASE_IMAGE, packages_to_install=COMPONENT_PACKAGES)
def split_data(
    processed_data: Input[Dataset],
    train_data: Output[Dataset],
    test_data: Output[Dataset],
):
    import pandas as pd
    from sklearn.model_selection import train_test_split

    df = pd.read_csv(processed_data.path)
    train_df, test_df = train_test_split(
        df,
        test_size=0.2,
        stratify=df["target"],
        random_state=42,
    )

    train_df.to_csv(train_data.path, index=False)
    test_df.to_csv(test_data.path, index=False)


@component(base_image=PYTHON_BASE_IMAGE, packages_to_install=COMPONENT_PACKAGES)
def train_model(train_data: Input[Dataset], model: Output[Model]):
    import joblib
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier

    df = pd.read_csv(train_data.path)
    X = df.drop("target", axis=1)
    y = df["target"]

    clf = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X, y)

    joblib.dump(clf, model.path)


@component(base_image=PYTHON_BASE_IMAGE, packages_to_install=COMPONENT_PACKAGES)
def evaluate_model(
    test_data: Input[Dataset],
    model: Input[Model],
    metrics: Output[Metrics],
):
    import joblib
    import pandas as pd
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score

    df = pd.read_csv(test_data.path)
    X = df.drop("target", axis=1)
    y = df["target"]

    clf = joblib.load(model.path)
    preds = clf.predict(X)
    pred_probs = clf.predict_proba(X)[:, 1]

    metrics.log_metric("accuracy", accuracy_score(y, preds))
    metrics.log_metric("precision", precision_score(y, preds, zero_division=0))
    metrics.log_metric("recall", recall_score(y, preds, zero_division=0))
    metrics.log_metric("f1_score", f1_score(y, preds, zero_division=0))
    metrics.log_metric("roc_auc", roc_auc_score(y, pred_probs))
    metrics.log_metric("test_rows", len(df))
    metrics.log_metric("test_fraud_rows", int(y.sum()))


@dsl.pipeline(name="fraud-detection-pipeline")
def fraud_detection_pipeline():
    load_task = load_data()

    preprocess_task = preprocess_data(
        input_data=load_task.outputs["output_data"],
    )

    split_task = split_data(
        processed_data=preprocess_task.outputs["processed_data"],
    )

    train_task = train_model(
        train_data=split_task.outputs["train_data"],
    )

    evaluate_model(
        test_data=split_task.outputs["test_data"],
        model=train_task.outputs["model"],
    )


if __name__ == "__main__":
    output_path = "fraud_big_split.yaml"
    print(f"Compiling pipeline to: {output_path}")
    compiler.Compiler().compile(
        pipeline_func=fraud_detection_pipeline,
        package_path=output_path,
    )
    print("Compilation finished")

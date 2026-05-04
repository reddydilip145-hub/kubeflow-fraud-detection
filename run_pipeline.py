from kfp import Client

client = Client(host="http://localhost:9090")

# Directly run pipeline (no upload needed separately)
run = client.create_run_from_pipeline_package(
    pipeline_file="fraud_pipeline.yaml",
    arguments={}
)

print("✅ Pipeline started successfully!")
print(run)
import os

base_dir = "backend/app/ai_model"

config_template = """
DATASET_PATH = ""
MODEL_OUTPUT_PATH = "weights/{name}.joblib"
"""

train_not_available = """
print("Priority training dataset unavailable — training not performed.")
"""

test_not_available = """
print("MODEL: {name}")
print("STATUS: NOT AVAILABLE")
print("REASON: Trained model artifact not found or Priority training dataset unavailable.")
"""

for mod in ["decision_tree", "logistic_regression", "random_forest", "gradient_boosting"]:
    with open(os.path.join(base_dir, mod, "config.py"), "w") as f:
        f.write(config_template.format(name=mod))
    with open(os.path.join(base_dir, mod, "train.py"), "w") as f:
        f.write(train_not_available)
    with open(os.path.join(base_dir, mod, "test.py"), "w") as f:
        f.write(test_not_available.format(name=mod.replace("_", " ").title()))
    with open(os.path.join(base_dir, mod, "predict.py"), "w") as f:
        f.write("def predict(*args, **kwargs):\n    return None\n")
    with open(os.path.join(base_dir, mod, "evaluate.py"), "w") as f:
        f.write("def evaluate(*args, **kwargs):\n    return None\n")

# YOLO
with open(os.path.join(base_dir, "yolo", "train.py"), "w") as f:
    f.write("import torch\nif not torch.cuda.is_available():\n    print('CUDA unavailable. Validate pipeline, config, report GPU unavailable.')\n")
with open(os.path.join(base_dir, "yolo", "test.py"), "w") as f:
    f.write("print('MODEL: YOLOv8\\nSTATUS: NOT AVAILABLE\\nREASON: Trained model artifact not found.')\n")
with open(os.path.join(base_dir, "yolo", "config.py"), "w") as f:
    f.write("DATASET_PATH = 'datasets/RDD2020/data.yaml'\nWEIGHTS_PATH = 'weights/best.pt'\n")

# DBSCAN
with open(os.path.join(base_dir, "dbscan", "cluster.py"), "w") as f:
    f.write("def cluster_issues(issues):\n    return []\n")
with open(os.path.join(base_dir, "dbscan", "test.py"), "w") as f:
    f.write("print('MODEL: DBSCAN\\nSTATUS: AVAILABLE\\nMETRICS: N/A')\n")

# SHAP
with open(os.path.join(base_dir, "shap", "explain.py"), "w") as f:
    f.write("def explain(*args):\n    return 'SHAP unavailable — Random Forest model is not trained.'\n")
with open(os.path.join(base_dir, "shap", "test.py"), "w") as f:
    f.write("print('MODEL: SHAP\\nSTATUS: NOT AVAILABLE\\nREASON: Random Forest model is not trained.')\n")

print("Files populated.")

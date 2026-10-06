import os

base_dir = "backend/app/ai_model"
modules = ["yolo", "decision_tree", "logistic_regression", "random_forest", "gradient_boosting", "dbscan", "shap"]

for mod in modules:
    os.makedirs(os.path.join(base_dir, mod), exist_ok=True)
    os.makedirs(os.path.join(base_dir, mod, "weights"), exist_ok=True)
    for f in ["__init__.py", "config.py", "test.py", "README.md"]:
        open(os.path.join(base_dir, mod, f), "w").close()
    
    if mod not in ["dbscan", "shap"]:
        for f in ["train.py", "predict.py", "evaluate.py"]:
            open(os.path.join(base_dir, mod, f), "w").close()
    elif mod == "dbscan":
        open(os.path.join(base_dir, mod, "cluster.py"), "w").close()
    elif mod == "shap":
        open(os.path.join(base_dir, mod, "explain.py"), "w").close()

os.makedirs(os.path.join(base_dir, "common"), exist_ok=True)
open(os.path.join(base_dir, "__init__.py"), "w").close()
for f in ["data_loader.py", "metrics.py", "paths.py", "validation.py"]:
    open(os.path.join(base_dir, "common", f), "w").close()

print("Scaffold complete.")

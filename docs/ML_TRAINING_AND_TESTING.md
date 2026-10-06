# ML Training and Testing Documentation

This document explains EXACTLY how to train and test EACH model independently.

## YOLOv8
**TRAIN:**
```cmd
cd /d E:\City_Care
python -m backend.app.ai_model.yolo.train
```

**TEST:**
```cmd
cd /d E:\City_Care
python -m backend.app.ai_model.yolo.test
```

## Decision Tree
**TRAIN:**
```cmd
cd /d E:\City_Care
python -m backend.app.ai_model.decision_tree.train
```

**TEST:**
```cmd
cd /d E:\City_Care
python -m backend.app.ai_model.decision_tree.test
```

## Logistic Regression
**TRAIN:**
```cmd
cd /d E:\City_Care
python -m backend.app.ai_model.logistic_regression.train
```

**TEST:**
```cmd
cd /d E:\City_Care
python -m backend.app.ai_model.logistic_regression.test
```

## Random Forest
**TRAIN:**
```cmd
cd /d E:\City_Care
python -m backend.app.ai_model.random_forest.train
```

**TEST:**
```cmd
cd /d E:\City_Care
python -m backend.app.ai_model.random_forest.test
```

## Gradient Boosting
**TRAIN:**
```cmd
cd /d E:\City_Care
python -m backend.app.ai_model.gradient_boosting.train
```

**TEST:**
```cmd
cd /d E:\City_Care
python -m backend.app.ai_model.gradient_boosting.test
```

## DBSCAN
**TEST:**
```cmd
cd /d E:\City_Care
python -m backend.app.ai_model.dbscan.test
```

## SHAP
**TEST:**
```cmd
cd /d E:\City_Care
python -m backend.app.ai_model.shap.test
```

import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.preprocessing import StandardScaler

class CivicVisionPriorityModels:
    def __init__(self, model_dir="backend/app/services/weights"):
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.feature_cols = [
            'issue_count', 'damage_area', 'detection_confidence', 'severity',
            'road_age_years', 'road_condition', 'traffic_volume', 'accident_history',
            'nearby_school', 'nearby_hospital', 'drainage_condition', 'days_since_maintenance'
        ]
        
        # Models
        self.models = {
            'decision_tree': DecisionTreeClassifier(random_state=42, max_depth=10),
            'logistic_regression': LogisticRegression(random_state=42, max_iter=1000),
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingClassifier(n_estimators=100, random_state=42)
        }
        
        self.scaler = StandardScaler()
        self.evaluation_results = {}
        
    def _get_model_path(self, model_name):
        return os.path.join(self.model_dir, f"{model_name}.joblib")
        
    def train_and_evaluate(self, df):
        """
        Trains and evaluates all 4 ML models as specified in CivicVision abstract.
        """
        X = df[self.feature_cols]
        y = df['priority_class']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale for Logistic Regression
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Save scaler
        joblib.dump(self.scaler, os.path.join(self.model_dir, "scaler.joblib"))
        
        for name, model in self.models.items():
            # Use scaled data for LR
            train_X = X_train_scaled if name == 'logistic_regression' else X_train
            test_X = X_test_scaled if name == 'logistic_regression' else X_test
            
            # Train
            model.fit(train_X, y_train)
            
            # Evaluate
            preds = model.predict(test_X)
            acc = accuracy_score(y_test, preds)
            prec = precision_score(y_test, preds, average='weighted', zero_division=0)
            rec = recall_score(y_test, preds, average='weighted', zero_division=0)
            f1 = f1_score(y_test, preds, average='weighted', zero_division=0)
            
            self.evaluation_results[name] = {
                'accuracy': round(acc, 4),
                'precision': round(prec, 4),
                'recall': round(rec, 4),
                'f1_score': round(f1, 4),
                'status': 'Trained'
            }
            
            # Save model
            joblib.dump(model, self._get_model_path(name))
            print(f"[ML] Trained {name}. Accuracy: {acc:.4f}")
            
        return self.evaluation_results

    def get_primary_model(self):
        """Returns the primary Random Forest model and the scaler"""
        rf_path = self._get_model_path('random_forest')
        scaler_path = os.path.join(self.model_dir, "scaler.joblib")
        
        if os.path.exists(rf_path) and os.path.exists(scaler_path):
            return joblib.load(rf_path), joblib.load(scaler_path)
        return None, None

    def predict_priority(self, features_dict):
        """
        Predicts priority using the primary Random Forest model.
        Falls back to rule-based basic if model not trained.
        """
        model, scaler = self.get_primary_model()
        
        # Prepare input
        input_data = []
        for col in self.feature_cols:
            input_data.append(features_dict.get(col, 0))
            
        df_input = pd.DataFrame([input_data], columns=self.feature_cols)
        
        if model is not None:
            prediction = model.predict(df_input)[0]
            
            probabilities = None
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(df_input)[0].tolist()
                
            return {
                "priority_class": int(prediction),
                "is_ml_prediction": True,
                "model_version": "random-forest-v1",
                "probabilities": probabilities,
                "status": "success"
            }
        else:
            return {
                "priority_class": None,
                "is_ml_prediction": False,
                "model_version": None,
                "status": "error",
                "reason": "Trained priority model not found. Training not executed because hardware/dataset availability is insufficient."
            }

if __name__ == "__main__":
    from app.ml.dataset import generate_synthetic_priority_dataset
    print("Generating dataset...")
    df = generate_synthetic_priority_dataset(2000)
    print("Training ML models...")
    ml_system = CivicVisionPriorityModels(model_dir="app/services/weights")
    results = ml_system.train_and_evaluate(df)
    print("Evaluation Results:", results)

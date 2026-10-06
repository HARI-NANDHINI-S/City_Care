try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
import pandas as pd
from app.ml.models import CivicVisionPriorityModels

class ShapExplainer:
    def __init__(self, model_dir="backend/app/services/weights"):
        self.models_mgr = CivicVisionPriorityModels(model_dir=model_dir)
        self.model, _ = self.models_mgr.get_primary_model()
        self.explainer = None
        
        if self.model is not None and HAS_SHAP:
            # We use TreeExplainer for Random Forest
            try:
                self.explainer = shap.TreeExplainer(self.model)
            except Exception as e:
                print(f"[SHAP] Warning: Could not initialize TreeExplainer. {e}")

    def explain_prediction(self, features_dict):
        """
        Returns feature importance for a single prediction.
        """
        if self.explainer is None:
            return {
                "available": False,
                "reason": "Model not trained or SHAP explainer could not be initialized."
            }
            
        feature_cols = self.models_mgr.feature_cols
        
        # Prepare input
        input_data = []
        for col in feature_cols:
            input_data.append(features_dict.get(col, 0))
            
        df_input = pd.DataFrame([input_data], columns=feature_cols)
        
        try:
            # Calculate SHAP values
            shap_values = self.explainer.shap_values(df_input)
            
            # For multi-class classification, shap_values is a list of arrays.
            # We need to find out which class was predicted to show the most relevant explanation.
            predicted_class = int(self.model.predict(df_input)[0])
            
            # Select the shap values for the predicted class
            if isinstance(shap_values, list):
                class_shap_values = shap_values[predicted_class][0]
            else:
                class_shap_values = shap_values[0]
                
            # Zip with feature names and sort by absolute impact
            feature_impacts = []
            for i, col in enumerate(feature_cols):
                feature_impacts.append({
                    "feature": col,
                    "value": float(df_input.iloc[0, i]),
                    "impact": float(class_shap_values[i]),
                    "abs_impact": abs(float(class_shap_values[i]))
                })
                
            # Sort by absolute impact descending
            feature_impacts.sort(key=lambda x: x["abs_impact"], reverse=True)
            
            return {
                "available": True,
                "predicted_class": predicted_class,
                "top_factors": feature_impacts[:5] # Return top 5 driving factors
            }
        except Exception as e:
            return {
                "available": False,
                "reason": f"Error calculating SHAP values: {str(e)}"
            }

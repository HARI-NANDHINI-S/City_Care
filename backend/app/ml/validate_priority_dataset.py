import os
import argparse
import pandas as pd

def validate_priority_dataset(csv_path):
    print(f"Validating Priority Dataset: {csv_path}")
    if not os.path.exists(csv_path):
        print(f"[ERROR] Priority dataset not found at {csv_path}")
        return False
        
    try:
        df = pd.read_csv(csv_path, comment='#')
    except Exception as e:
        print(f"[ERROR] Could not read CSV: {e}")
        return False
        
    expected_cols = [
        'issue_count', 'damage_area', 'detection_confidence', 'severity',
        'road_age_years', 'road_condition', 'traffic_volume', 'accident_history',
        'nearby_school', 'nearby_hospital', 'drainage_condition', 'days_since_maintenance',
        'priority_class'
    ]
    
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        print(f"[ERROR] Missing columns: {missing_cols}")
        return False
        
    print(f"[INFO] Found {len(df)} records.")
    
    # Check for missing values
    missing_vals = df.isnull().sum().sum()
    if missing_vals > 0:
        print(f"[WARNING] Dataset contains {missing_vals} missing values.")
        
    # Check class distribution
    if 'priority_class' in df.columns:
        print(f"[INFO] Class distribution:")
        print(df['priority_class'].value_counts().to_string())
        
    print("\nPriority Dataset Validation: PASSED")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, required=True, help="Path to priority dataset CSV")
    args = parser.parse_args()
    validate_priority_dataset(args.data)

import os
import sys
import json

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai_model.random_forest.predict import predict as rf_predict

def test_rf():
    print("=== Random Forest Direct Integration Test ===")
    
    # 1. Valid Features
    valid_payload = {
        "PCI": 65.0,
        "AADT": 15000,
        "Last Maintenance": 2.5,
        "Average Rainfall": 120.5,
        "Rutting": 5.2,
        "IRI": 2.1,
        "Road Type": "Arterial",
        "Asphalt Type": "HMA"
    }
    res = rf_predict(valid_payload)
    print("\n[+] Valid Features:")
    print(json.dumps(res, indent=2))
    
    # 2. Missing/Empty Features
    res = rf_predict({})
    print("\n[+] Missing Features:")
    print(json.dumps(res, indent=2))
    
    # 3. Partial Features
    partial_payload = {
        "PCI": 65.0,
        "AADT": 15000
    }
    res = rf_predict(partial_payload)
    print("\n[+] Partial Features:")
    print(json.dumps(res, indent=2))

    # 4. Invalid Features
    invalid_payload = {
        "PCI": "STRING_NOT_FLOAT",
        "AADT": 15000,
        "Last Maintenance": 2.5,
        "Average Rainfall": 120.5,
        "Rutting": 5.2,
        "IRI": 2.1,
        "Road Type": "Arterial",
        "Asphalt Type": "HMA"
    }
    res = rf_predict(invalid_payload)
    print("\n[+] Invalid Features (Type Mismatch):")
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    test_rf()

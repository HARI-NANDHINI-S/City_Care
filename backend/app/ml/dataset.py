import pandas as pd
import numpy as np

def generate_synthetic_priority_dataset(num_samples=2000):
    """
    Generates a synthetic structured dataset for training priority ML models
    as specified in the CivicVision AI abstract.
    """
    np.random.seed(42)
    
    # Features
    # detection features
    issue_count = np.random.randint(1, 10, num_samples)
    damage_area = np.random.uniform(0.01, 0.5, num_samples)
    detection_confidence = np.random.uniform(0.6, 0.99, num_samples)
    
    # severity (0=LOW, 1=MEDIUM, 2=HIGH, 3=CRITICAL) mapped later for clarity
    severity = np.random.choice([0, 1, 2, 3], num_samples, p=[0.4, 0.3, 0.2, 0.1])
    
    # road features
    road_age_years = np.random.randint(1, 30, num_samples)
    # road condition (0=Poor, 1=Fair, 2=Good)
    road_condition = np.random.choice([0, 1, 2], num_samples)
    
    # traffic features (vehicles per day)
    traffic_volume = np.random.randint(100, 20000, num_samples)
    
    # safety features
    accident_history = np.random.poisson(lam=1, size=num_samples)
    nearby_school = np.random.choice([0, 1], num_samples, p=[0.8, 0.2])
    nearby_hospital = np.random.choice([0, 1], num_samples, p=[0.9, 0.1])
    
    # environmental/drainage (0=Poor, 1=Good)
    drainage_condition = np.random.choice([0, 1], num_samples)
    
    # maintenance history (days since last maintenance)
    days_since_maintenance = np.random.randint(30, 3650, num_samples)

    df = pd.DataFrame({
        'issue_count': issue_count,
        'damage_area': damage_area,
        'detection_confidence': detection_confidence,
        'severity': severity,
        'road_age_years': road_age_years,
        'road_condition': road_condition,
        'traffic_volume': traffic_volume,
        'accident_history': accident_history,
        'nearby_school': nearby_school,
        'nearby_hospital': nearby_hospital,
        'drainage_condition': drainage_condition,
        'days_since_maintenance': days_since_maintenance
    })

    # Rule-based priority generation (to have something the ML models can learn)
    # Higher score = higher priority
    base_score = (
        (df['severity'] * 20) + 
        (df['damage_area'] * 40) + 
        (df['traffic_volume'] / 1000) * 1.5 + 
        (df['accident_history'] * 10) + 
        (df['nearby_school'] * 15) + 
        (df['nearby_hospital'] * 20) + 
        (df['road_age_years'] * 0.5) +
        ((1 - df['drainage_condition']) * 10)
    )
    
    # Add some noise
    noise = np.random.normal(0, 10, num_samples)
    final_score = base_score + noise
    
    # Map score to classes: 0=LOW, 1=MEDIUM, 2=HIGH, 3=CRITICAL
    q33 = np.percentile(final_score, 33)
    q66 = np.percentile(final_score, 66)
    q90 = np.percentile(final_score, 90)
    
    def map_priority(score):
        if score > q90: return 3 # CRITICAL
        if score > q66: return 2 # HIGH
        if score > q33: return 1 # MEDIUM
        return 0 # LOW
        
    df['priority_class'] = final_score.apply(map_priority)
    
    return df

if __name__ == "__main__":
    df = generate_synthetic_priority_dataset()
    print("Dataset shape:", df.shape)
    print(df['priority_class'].value_counts())

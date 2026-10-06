def get_maintenance_recommendation(priority_class: int, issue_type: str, features: dict = None) -> str:
    """
    Generates a contextual maintenance recommendation based on the ML priority classification
    and issue details as specified in the CivicVision AI project document.
    
    priority_class: 0 (LOW), 1 (MEDIUM), 2 (HIGH), 3 (CRITICAL)
    """
    
    if priority_class == 3: # CRITICAL
        base = "Immediate inspection and repair required."
        if issue_type == "Open Manhole":
            return f"{base} Dispatch emergency barricade unit immediately to prevent severe accidents."
        elif issue_type == "Pothole" and features and features.get("traffic_volume", 0) > 5000:
            return f"{base} High traffic volume detected. Schedule emergency night repair to minimize traffic disruption."
        return base
        
    elif priority_class == 2: # HIGH
        base = "Prioritize maintenance team assignment."
        if issue_type == "Waterlogging":
            return f"{base} Dispatch drainage clearing truck to prevent further road damage."
        elif features and features.get("nearby_school", 0) == 1:
            return f"{base} Sensitive location (school) nearby. Clear hazard before next active hours."
        return f"{base} Schedule repair within 48 hours."
        
    elif priority_class == 1: # MEDIUM
        base = "Schedule maintenance inspection."
        if issue_type == "Broken Streetlight":
            return f"{base} Add to regular electrical maintenance route within 5 days."
        return f"{base} Incorporate into upcoming neighborhood repair cycle (1-2 weeks)."
        
    else: # LOW
        return "Routine monitoring. Add to scheduled seasonal inspection list."

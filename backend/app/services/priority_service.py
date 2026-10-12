from app.models.issue import IssueType, SeverityLevel
from app.core.config import settings
from app.core.defect_registry import DEFECT_REGISTRY

CATEGORY_RISK_SCORES = {
    # Drainage
    IssueType.DAMAGED_DRAINAGE_COVER: 90.0,
    IssueType.WATERLOGGING: 80.0,
    IssueType.OVERFLOWING_DRAIN: 80.0,
    IssueType.BLOCKED_DRAIN: 75.0,

    # Road
    IssueType.POTHOLE: 75.0,
    IssueType.ALLIGATOR_CRACK: 70.0,
    IssueType.DAMAGED_ROAD_SURFACE: 65.0,
    IssueType.ROAD_DAMAGE: 65.0,
    IssueType.LONGITUDINAL_CRACK: 60.0,
    IssueType.TRANSVERSE_CRACK: 60.0,

    # Sanitation
    IssueType.ILLEGAL_DUMPING: 55.0,
    IssueType.OVERFLOWING_BINS: 52.0,
    IssueType.GARBAGE: 50.0,

    # Utility
    IssueType.MANHOLE: 95.0,
    IssueType.STREETLIGHT: 50.0,
}

def calculate_category_risk(issue_type: str) -> float:
    # 1. Check registry
    reg = DEFECT_REGISTRY.get(str(issue_type))
    if reg and "base_risk_score" in reg:
        return reg["base_risk_score"]

    # 2. Check IssueType enums
    for key, score in CATEGORY_RISK_SCORES.items():
        if key.value.lower() == str(issue_type).lower() or key.name.lower() == str(issue_type).lower():
            return score
    return 50.0

def calculate_priority_score(
    issue_type: str,
    ai_confidence: float,
    defect_area_ratio: float = 0.0,
    duplicate_count: int = 0,
    hours_unresolved: float = 0.0
) -> float:
    """
    Calculate an explainable priority score between 0 and 100 based on weighted factors.
    """
    s_cat = calculate_category_risk(issue_type)
    s_conf = min(100.0, max(0.0, ai_confidence * 100.0 if ai_confidence <= 1.0 else ai_confidence))
    s_area = min(100.0, max(0.0, defect_area_ratio * 100.0 if defect_area_ratio <= 1.0 else defect_area_ratio))
    s_dup = min(100.0, duplicate_count * 20.0)
    s_age = min(100.0, hours_unresolved * 1.5)

    raw_score = (
        settings.WEIGHT_CATEGORY * s_cat +
        settings.WEIGHT_CONFIDENCE * s_conf +
        settings.WEIGHT_DEFECT_AREA * s_area +
        settings.WEIGHT_DUPLICATES * s_dup +
        settings.WEIGHT_AGING * s_age
    )

    final_score = round(min(100.0, max(0.0, raw_score)), 1)
    return final_score

def get_severity_from_priority(priority_score: float) -> SeverityLevel:
    if priority_score <= 30.0:
        return SeverityLevel.LOW
    elif priority_score <= 60.0:
        return SeverityLevel.MEDIUM
    elif priority_score <= 80.0:
        return SeverityLevel.HIGH
    else:
        return SeverityLevel.CRITICAL

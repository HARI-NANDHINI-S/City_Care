import math
from datetime import datetime, timedelta
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models.issue import Issue, IssueStatus
from app.models.duplicate import DuplicateIssueRelation
from app.core.config import settings

EARTH_RADIUS_METERS = 6371000.0  # Earth radius in meters

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates distance between two coordinates in meters using Haversine formula."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    return EARTH_RADIUS_METERS * c

def find_spatial_duplicates(
    db: Session,
    latitude: float,
    longitude: float,
    issue_type: str,
    radius_meters: float = None,
    time_window_hours: float = None
) -> List[Tuple[Issue, float]]:
    """
    Find existing non-resolved issues with matching category within specified distance and time window.
    Returns list of tuples (Issue, distance_in_meters).
    """
    if radius_meters is None:
        radius_meters = settings.DUPLICATE_RADIUS_METERS
    if time_window_hours is None:
        time_window_hours = settings.DUPLICATE_TIME_WINDOW_HOURS

    cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)

    candidate_issues = db.query(Issue).filter(
        Issue.issue_type == issue_type,
        Issue.status != IssueStatus.RESOLVED,
        Issue.created_at >= cutoff_time
    ).all()

    duplicates = []
    for candidate in candidate_issues:
        dist = calculate_haversine_distance(latitude, longitude, candidate.latitude, candidate.longitude)
        if dist <= radius_meters:
            duplicates.append((candidate, round(dist, 1)))

    return duplicates

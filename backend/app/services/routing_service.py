from app.models.issue import IssueType
from app.core.defect_registry import DEFECT_REGISTRY

# Base Department Routing Map
DEPARTMENT_ROUTING_MAP = {
    # Road defects
    IssueType.POTHOLE: "DEPT_PWD",
    IssueType.LONGITUDINAL_CRACK: "DEPT_PWD",
    IssueType.TRANSVERSE_CRACK: "DEPT_PWD",
    IssueType.ALLIGATOR_CRACK: "DEPT_PWD",
    IssueType.DAMAGED_ROAD_SURFACE: "DEPT_PWD",
    IssueType.ROAD_DAMAGE: "DEPT_PWD",

    # Sanitation defects
    IssueType.GARBAGE: "DEPT_SAN",
    IssueType.ILLEGAL_DUMPING: "DEPT_SAN",
    IssueType.OVERFLOWING_BINS: "DEPT_SAN",

    # Drainage defects
    IssueType.BLOCKED_DRAIN: "DEPT_DRAIN",
    IssueType.OVERFLOWING_DRAIN: "DEPT_DRAIN",
    IssueType.WATERLOGGING: "DEPT_DRAIN",
    IssueType.DAMAGED_DRAINAGE_COVER: "DEPT_DRAIN",

    # Utility defects
    IssueType.STREETLIGHT: "DEPT_ELEC",
    IssueType.MANHOLE: "DEPT_SEW",
}

DEPARTMENT_NAME_MAP = {
    "DEPT_PWD": "Road & Public Works Department",
    "DEPT_SAN": "Waste Management & Sanitation Dept",
    "DEPT_ELEC": "Electrical Infrastructure Dept",
    "DEPT_DRAIN": "Stormwater Drainage Dept",
    "DEPT_SEW": "Sewerage & Sanitation Board",
}

def get_recommended_department_code(issue_type: str) -> str:
    """Returns department code based on issue type string or Enum."""
    # 1. Check registry first
    reg = DEFECT_REGISTRY.get(str(issue_type))
    if reg:
        return reg["default_dept_code"]

    # 2. Check IssueType enums
    for key, dept_code in DEPARTMENT_ROUTING_MAP.items():
        if key.value.lower() == str(issue_type).lower() or key.name.lower() == str(issue_type).lower():
            return dept_code
    return "DEPT_PWD"

def get_recommended_department_name(issue_type: str) -> str:
    code = get_recommended_department_code(issue_type)
    return DEPARTMENT_NAME_MAP.get(code, "Road & Public Works Department")

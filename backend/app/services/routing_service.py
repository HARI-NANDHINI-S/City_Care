from app.models.issue import IssueType

# Configurable Department Routing Matrix
DEPARTMENT_ROUTING_MAP = {
    IssueType.POTHOLE: "DEPT_PWD",
    IssueType.ROAD_DAMAGE: "DEPT_PWD",
    IssueType.GARBAGE: "DEPT_SAN",
    IssueType.STREETLIGHT: "DEPT_ELEC",
    IssueType.WATERLOGGING: "DEPT_DRAIN",
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
    for key, dept_code in DEPARTMENT_ROUTING_MAP.items():
        if key.value.lower() == str(issue_type).lower() or key.name.lower() == str(issue_type).lower():
            return dept_code
    return "DEPT_PWD"

def get_recommended_department_name(issue_type: str) -> str:
    code = get_recommended_department_code(issue_type)
    return DEPARTMENT_NAME_MAP.get(code, "Road & Public Works Department")

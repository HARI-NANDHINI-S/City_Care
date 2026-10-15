import os
import math
from typing import List, Union, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CivicVision AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Computer Vision / ML Feature Flags (Disabled by default)
    ENABLE_IRDID_CLASSIFIER: bool = False

    @field_validator("ENABLE_IRDID_CLASSIFIER", mode="before")
    @classmethod
    def validate_enable_irdid_classifier(cls, v: Any) -> bool:
        """
        Fail-safe boolean parsing for ENABLE_IRDID_CLASSIFIER:
        Missing, malformed, or invalid values safely default to False.
        """
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            val = v.strip().lower()
            if val in ("true", "1", "yes", "on", "enabled"):
                return True
            return False
        if isinstance(v, (int, float)):
            return bool(v)
        return False
    
    # Computer Vision Confidence Thresholds (Evidence-based defaults)
    YOLO_CONFIDENCE_THRESHOLD: float = 0.25
    IRDID_CLASSIFIER_THRESHOLD: float = 0.30

    @field_validator("YOLO_CONFIDENCE_THRESHOLD", mode="before")
    @classmethod
    def validate_yolo_threshold(cls, v: Any) -> float:
        """
        Fail-safe float parsing for YOLO_CONFIDENCE_THRESHOLD:
        Must be a valid finite float between 0.05 and 0.95.
        Invalid, out-of-range, or non-finite values safely default to 0.25.
        """
        DEFAULT_YOLO_THRESH = 0.25
        if v is None:
            return DEFAULT_YOLO_THRESH
        try:
            val = float(v)
            if not math.isfinite(val):
                return DEFAULT_YOLO_THRESH
            if 0.05 <= val <= 0.95:
                return round(val, 4)
            return DEFAULT_YOLO_THRESH
        except (TypeError, ValueError):
            return DEFAULT_YOLO_THRESH

    @field_validator("IRDID_CLASSIFIER_THRESHOLD", mode="before")
    @classmethod
    def validate_irdid_threshold(cls, v: Any) -> float:
        """
        Fail-safe float parsing for IRDID_CLASSIFIER_THRESHOLD:
        Must be a valid finite float between 0.10 and 0.95.
        Invalid, out-of-range, or non-finite values safely default to 0.30.
        """
        DEFAULT_IRDID_THRESH = 0.30
        if v is None:
            return DEFAULT_IRDID_THRESH
        try:
            val = float(v)
            if not math.isfinite(val):
                return DEFAULT_IRDID_THRESH
            if 0.10 <= val <= 0.95:
                return round(val, 4)
            return DEFAULT_IRDID_THRESH
        except (TypeError, ValueError):
            return DEFAULT_IRDID_THRESH
    
    # Secret Key & JWT Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database Configuration (Defaults to SQLite for seamless local dev; can set PostgreSQL DATABASE_URL in .env)
    DATABASE_URL: str = "sqlite:///./civicvision.db"
    
    # Storage Paths & Upload Limits
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "uploads")
    ORIGINAL_IMG_DIR: str = os.path.join(UPLOAD_DIR, "original")
    ANNOTATED_IMG_DIR: str = os.path.join(UPLOAD_DIR, "annotated")
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MiB limit (10,485,760 bytes)
    
    # CORS Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Priority Scoring Engine Weights
    WEIGHT_CATEGORY: float = 0.35
    WEIGHT_CONFIDENCE: float = 0.15
    WEIGHT_DEFECT_AREA: float = 0.15
    WEIGHT_DUPLICATES: float = 0.20
    WEIGHT_AGING: float = 0.15
    
    # Duplicate Detection Parameters
    DUPLICATE_RADIUS_METERS: float = 50.0  # meters
    DUPLICATE_TIME_WINDOW_HOURS: float = 72.0  # hours
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Ensure upload directories exist
os.makedirs(settings.ORIGINAL_IMG_DIR, exist_ok=True)
os.makedirs(settings.ANNOTATED_IMG_DIR, exist_ok=True)

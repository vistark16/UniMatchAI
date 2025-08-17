from pydantic import BaseModel, Field, conint, confloat
from typing import Optional, Literal, List

class PredictRequest(BaseModel):
    program: Literal["saintek", "soshum"]
    
    # Legacy fields (for backward compatibility)
    target_major: Optional[str] = None
    
    # New university-major selection fields
    target_university: Optional[str] = None
    target_university_1: Optional[str] = None
    target_university_2: Optional[str] = None
    target_university_3: Optional[str] = None
    
    target_major_1: Optional[str] = None
    target_major_2: Optional[str] = None
    target_major_3: Optional[str] = None
    
    # Array fields for multiple selections
    target_universities: Optional[List[str]] = None
    target_majors: Optional[List[str]] = None
    
    competitiveness: Literal["very", "high", "mid", "low"]
    
    # semester grades 0–100; allow missing to simulate incomplete inputs
    s1: Optional[confloat(ge=0, le=100)] = None
    s2: Optional[confloat(ge=0, le=100)] = None
    s3: Optional[confloat(ge=0, le=100)] = None
    s4: Optional[confloat(ge=0, le=100)] = None
    s5: Optional[confloat(ge=0, le=100)] = None

    # core subjects mean (0–100)
    math: Optional[confloat(ge=0, le=100)] = None
    language: Optional[confloat(ge=0, le=100)] = None  # id+en avg (optional)

    # saintek-only
    physics: Optional[confloat(ge=0, le=100)] = None
    chemistry: Optional[confloat(ge=0, le=100)] = None
    biology: Optional[confloat(ge=0, le=100)] = None

    # soshum-only
    economics: Optional[confloat(ge=0, le=100)] = None
    geography: Optional[confloat(ge=0, le=100)] = None
    history: Optional[confloat(ge=0, le=100)] = None

    rank_percentile: conint(ge=1, le=100) = Field(100, description="e.g., 10 means Top10%")
    achievement: Literal["none", "school", "prov", "national"] = "none"
    accreditation: Literal["A", "B", "C"] = "B"

class PredictResponse(BaseModel):
    probability: float
    label: Literal["low", "medium", "high"]
    details: dict
    tips: list[str]
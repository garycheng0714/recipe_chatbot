from enum import StrEnum

from pydantic import BaseModel, Field


class DistanceProfile(StrEnum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class ElevationDensityProfile(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class TechnicalityProfile(StrEnum):
    NON_TECHNICAL = "non_technical"
    MODERATE = "moderate"
    TECHNICAL = "technical"


class TerrainType(StrEnum):
    ROAD = "road"
    DIRT = "dirt"
    ROCK = "rock"
    MIXED = "mixed"


class ElevationProfile(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class NeedsClarification(BaseModel):
    """資訊不足時回傳,不會觸發任何工具"""
    question: str = Field(description="要問使用者的澄清問題")


class RouteSearchRequest(BaseModel):
    """條件齊全後才會產生的結構,用來呼叫查詢工具"""
    location: str = Field(description="Location of the route.")
    distance_min_km: float | None = Field(description="Minimum distance in km.")
    distance_max_km: float | None = Field(description="Maximum distance in km.")
    elevation_gain_m: float = Field(
        description="""
        Elevation gain in m.
        
        Only populate this field when the user explicitly provides a numeric elevation gain requirement.
        """
    )
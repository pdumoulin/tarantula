from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ChromecastStartBody(BaseModel):
    url: str
    mime_type: str


class ChromecastSeekBody(BaseModel):
    time: float


class ChromecastSeekByBody(BaseModel):
    seconds: float


class PatchPlugBody(BaseModel):
    name: Optional[str] = None
    status: Optional[bool] = None


class PlugResponse(BaseModel):
    id: int
    name: str | None
    status: bool | None


class Routine(Enum):
    BEDTIME = "bedtime"
    SLEEPTIME = "sleeptime"
    WAKETIME = "waketime"

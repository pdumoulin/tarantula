from enum import Enum
from typing import Optional

from pydantic import BaseModel


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

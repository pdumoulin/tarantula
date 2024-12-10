"""Internal application data models."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class PatchPlugBody(BaseModel):
    """Plug action details."""

    name: Optional[str] = None
    status: Optional[bool] = None


class PlugResponse(BaseModel):
    """Plug response format."""

    id: int
    name: str | None
    status: bool | None


class Routine(Enum):
    """Available routines."""

    BEDTIME = 'bedtime'
    SLEEPTIME = 'sleeptime'
    WAKETIME = 'waketime'

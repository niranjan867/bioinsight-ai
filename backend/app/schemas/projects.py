from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: str | None = Field(None, description="Optional project description")
    status: str = Field(default="active", pattern="^(active|archived|completed)$")
    tags: list[str] | None = Field(default=None, description="Keywords or taxonomy tags")


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = Field(None, pattern="^(active|archived|completed)$")
    tags: list[str] | None = None


class ProjectItemCreate(BaseModel):
    item_type: str = Field(
        ...,
        pattern="^(gene|protein|compound|disease|sequence|note|structure|docking)$",
        description="Type of scientific entity",
    )
    item_id: str = Field(..., min_length=1, max_length=128, description="Target identifier or symbol")
    title: str = Field(..., min_length=1, max_length=255, description="Display title")
    description: str | None = None
    metadata_json: dict[str, Any] | None = None


class ProjectItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    item_type: str
    item_id: str
    title: str
    description: str | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime


class ProjectActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    user_id: int
    action: str
    details: dict[str, Any] | None = None
    created_at: datetime


class ProjectSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    description: str | None = None
    status: str
    tags: list[str] | None = None
    items_count: int = 0
    created_at: datetime
    updated_at: datetime


class ProjectDetailResponse(ProjectSummaryResponse):
    items: list[ProjectItemResponse] = []
    activities: list[ProjectActivityResponse] = []

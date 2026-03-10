from datetime import datetime

from pydantic import BaseModel


class CategoryOut(BaseModel):
    id: str
    name: str


class DomainOut(BaseModel):
    id: str
    name: str


class TechStackOut(BaseModel):
    id: str
    name: str
    icon_url: str
    type: str


class ProjectOut(BaseModel):
    id: str
    title: str
    description: str | None = None
    repo_url: str | None = None
    published: bool = False
    trending: bool = False
    logo_url: str | None = None
    categories: list[CategoryOut] = []
    domains: list[DomainOut] = []
    tech_stacks: list[TechStackOut] = []


class ProjectSimilarOut(BaseModel):
    id: str
    title: str
    description: str | None = None
    repo_url: str | None = None
    similarity: float


class TrendingProjectOut(BaseModel):
    project_id: str
    stars: int | None = None
    last_synced_at: datetime | None = None


class ErrorOut(BaseModel):
    detail: str

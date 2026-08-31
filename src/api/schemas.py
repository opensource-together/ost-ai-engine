from datetime import date, datetime

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


class ProjectSemanticOut(BaseModel):
    id: str
    title: str
    description: str | None = None
    repo_url: str | None = None
    logo_url: str | None = None
    similarity: float


class TrendingProjectOut(BaseModel):
    project_id: str
    stars: int | None = None
    last_synced_at: datetime | None = None


class GithubTrendingProjectOut(BaseModel):
    repo_url: str
    stars_today: int | None = None
    trending_date: date
    name: str
    full_name: str
    description: str | None = None
    stars: int | None = None
    language: str | None = None
    linked_project_id: str | None = None
    category_id: str | None = None
    domain_id: str | None = None


class ForYouProjectOut(BaseModel):
    project_id: str
    title: str
    description: str | None = None
    repo_url: str | None = None
    similarity_score: float
    preference_score: float
    freshness_score: float
    popularity_score: float
    final_score: float


class ErrorOut(BaseModel):
    detail: str

from pydantic import Field
from pydantic_settings import BaseSettings


class APIConfig(BaseSettings):
    """API configuration loaded from environment variables."""

    database_url: str = Field(alias="DATABASE_URL")
    host: str = Field(default="0.0.0.0", alias="API_HOST")
    port: int = Field(default=8000, alias="API_PORT")
    rate_limit: int = Field(default=60, alias="API_RATE_LIMIT")
    service_token: str | None = Field(default=None, alias="OST_LINKER_SERVICE_TOKEN")

    model_config = {"populate_by_name": True}

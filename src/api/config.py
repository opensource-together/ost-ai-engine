from pydantic import Field
from pydantic_settings import BaseSettings


class APIConfig(BaseSettings):
    """API settings from environment (DATABASE_URL, API_*, optional service token)."""

    database_url: str = Field(alias="DATABASE_URL")
    host: str = Field(default="0.0.0.0", alias="API_HOST")
    port: int = Field(default=8000, alias="API_PORT")
    rate_limit: int = Field(default=60, alias="API_RATE_LIMIT")
    service_token: str | None = Field(default=None, alias="OST_LINKER_SERVICE_TOKEN")
    require_service_token: bool = Field(
        default=False,
        alias="OST_LINKER_REQUIRE_SERVICE_TOKEN",
    )

    model_config = {"populate_by_name": True}

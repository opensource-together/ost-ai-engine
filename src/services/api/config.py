from pydantic import Field
from pydantic_settings import BaseSettings


class APIConfig(BaseSettings):
    """API configuration.
    
    This module defines `APIConfig`, a `BaseSettings` class that loads API
    configuration from environment variables. It is used to configure the API
    service, including the database URL, host, port, rate limit, and service
    token.
    """

    database_url: str = Field(alias="DATABASE_URL")
    host: str = Field(default="0.0.0.0", alias="API_HOST")
    port: int = Field(default=8000, alias="API_PORT")
    rate_limit: int = Field(default=60, alias="API_RATE_LIMIT")
    service_token: str | None = Field(default=None, alias="OST_LINKER_SERVICE_TOKEN")

    # may paydantic to use this to populate the config and construct the model
    # using the field name as the environment variable name
    # e.g. DATABASE_URL -> database_url
    model_config = {"populate_by_name": True}

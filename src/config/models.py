from os import getenv
from pydantic import BaseModel, Field, field_validator, HttpUrl, ValidationInfo, ConfigDict


class RateLimitConfig(BaseModel):
    """Controls how many requests can be made to the endpoint to prevent abuse and manage infrastructure costs"""
    model_config = ConfigDict(extra='forbid')

    min_delay_s: float = Field(ge=0.5, description="Minimum delay between requests (seconds)")
    max_delay_s: float = Field(ge=0.5, description="Maximum delay between requests (seconds)")
    max_requests: int = Field(default=5, description="Max requests per period")
    period_seconds: int = Field(default=2, description="Time window for max_requests")

    @field_validator('max_delay_s')
    @classmethod
    def compare_delays(cls, value, info: ValidationInfo):
        if 'min_delay_s' in info.data and value < info.data['min_delay_s']:
            raise ValueError('max_delay_s must be >= min_delay_s')
        return value


class PaginationConfig(BaseModel):
    """Pagination settings for multi-page scraping"""
    model_config = ConfigDict(extra='forbid')

    enabled: bool = True
    param_name: str = "page"
    start_page: int = 1
    max_pages: int = Field(default=1, ge=0, description="0 = no limit")
    page_size: int = 100
    stop_on_empty: bool = True


class SourceConfig(BaseModel):
    """Configuration for single source in config/sources.yaml"""
    model_config = ConfigDict(extra='forbid')

    base_url: HttpUrl
    rate_limit: RateLimitConfig
    pagination: PaginationConfig = Field(default_factory=PaginationConfig)
    enabled: bool = True
    query: str = ""
    headers_file: str | None = None
    parser_type: str = "html_bs4"

    @field_validator('base_url', mode='before')
    @classmethod
    def resolve_env_vars(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith('${') and v.endswith('}'):
            env_var_name = v[2:-1]  # get variable name without ${ and }
            resolved_value = getenv(env_var_name)

            if not resolved_value:
                raise ValueError(f"Environment variable '{env_var_name}' is not set in .env file")
            return resolved_value

        return v


class SourcesConfig(BaseModel):
    """Aggregated Sources Configuration in config/sources.yaml"""
    model_config = ConfigDict(extra='forbid')

    sources: dict[str, SourceConfig]
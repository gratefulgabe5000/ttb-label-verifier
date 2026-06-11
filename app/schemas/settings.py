from pydantic import BaseModel, Field


class ApiKeyUpdateRequest(BaseModel):
    api_key: str = Field(min_length=1, description="Anthropic API key (e.g. sk-ant-...)")


class ApiKeyStatusResponse(BaseModel):
    configured: bool
    masked_key: str | None = None
    connected: bool = False
    message: str | None = None

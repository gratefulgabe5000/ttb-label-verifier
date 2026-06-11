from fastapi import APIRouter, Depends

from dependencies import get_current_agent
from schemas.settings import ApiKeyStatusResponse, ApiKeyUpdateRequest
from services import settings_service

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(get_current_agent)])


@router.get("/api-key", response_model=ApiKeyStatusResponse)
def get_api_key_status() -> ApiKeyStatusResponse:
    if not settings_service.is_configured():
        return ApiKeyStatusResponse(configured=False)

    connected, message = settings_service.test_connection()
    return ApiKeyStatusResponse(
        configured=True,
        masked_key=settings_service.get_masked_key(),
        connected=connected,
        message=message,
    )


@router.put("/api-key", response_model=ApiKeyStatusResponse)
def set_api_key(payload: ApiKeyUpdateRequest) -> ApiKeyStatusResponse:
    settings_service.set_api_key(payload.api_key)
    connected, message = settings_service.test_connection()
    return ApiKeyStatusResponse(
        configured=True,
        masked_key=settings_service.get_masked_key(),
        connected=connected,
        message=message,
    )


@router.delete("/api-key", response_model=ApiKeyStatusResponse)
def delete_api_key() -> ApiKeyStatusResponse:
    settings_service.clear_api_key()
    return ApiKeyStatusResponse(configured=False)

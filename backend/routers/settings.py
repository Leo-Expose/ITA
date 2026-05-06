"""Settings API — manage API keys and LLM provider config from the UI."""

from fastapi import APIRouter
from pydantic import BaseModel
from backend.settings_manager import (
    get_api_keys_status,
    save_api_key,
    test_api_key,
    get_llm_config,
    save_llm_config,
    apply_llm_config_to_default,
    PROVIDERS_INFO,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


class ApiKeyUpdate(BaseModel):
    provider: str
    key: str


class ApiKeyTest(BaseModel):
    provider: str
    key: str | None = None  # if None, tests saved key


class LLMConfigUpdate(BaseModel):
    llm_provider: str | None = None
    deep_think_llm: str | None = None
    quick_think_llm: str | None = None


@router.get("/api-keys")
def list_api_keys():
    """Get status of all API keys (masked)."""
    return get_api_keys_status()


@router.put("/api-keys")
def update_api_key(data: ApiKeyUpdate):
    """Save a new API key."""
    save_api_key(data.provider, data.key)
    return {"status": "saved", "provider": data.provider}


@router.delete("/api-keys/{provider}")
def delete_api_key(provider: str):
    """Remove an API key from DB (env var fallback still applies)."""
    save_api_key(provider, "")
    return {"status": "removed", "provider": provider}


@router.post("/api-keys/test")
def test_key(data: ApiKeyTest):
    """Test if an API key works."""
    return test_api_key(data.provider, data.key)


@router.get("/llm")
def get_llm_settings():
    """Get current LLM provider and model settings."""
    return get_llm_config()


@router.put("/llm")
def update_llm_settings(data: LLMConfigUpdate):
    """Update LLM provider/model settings."""
    save_llm_config(
        provider=data.llm_provider,
        deep_model=data.deep_think_llm,
        quick_model=data.quick_think_llm,
    )
    apply_llm_config_to_default()
    return {"status": "saved", "config": get_llm_config()}


@router.get("/providers")
def list_providers():
    """List available LLM providers with their supported models."""
    return PROVIDERS_INFO

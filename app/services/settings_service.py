"""Runtime management of the agent-supplied Anthropic API key.

Per IA-02 (revised): rather than baking ANTHROPIC_API_KEY into the deployment
environment ahead of time, the logged-in agent supplies it via the frontend
Settings panel. It is stored only in this process's environment for the
lifetime of the process — never written to disk, `.env`, or the database.
Restarting the server clears it and the agent must re-enter it.
"""

import os

from anthropic import Anthropic, AuthenticationError

API_KEY_ENV_VAR = "ANTHROPIC_API_KEY"


def _mask(key: str) -> str:
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:6]}{'*' * 8}{key[-4:]}"


def is_configured() -> bool:
    return bool(os.environ.get(API_KEY_ENV_VAR))


def get_masked_key() -> str | None:
    key = os.environ.get(API_KEY_ENV_VAR)
    return _mask(key) if key else None


def set_api_key(api_key: str) -> None:
    os.environ[API_KEY_ENV_VAR] = api_key.strip()


def clear_api_key() -> None:
    os.environ.pop(API_KEY_ENV_VAR, None)


def test_connection() -> tuple[bool, str]:
    """Make a lightweight, no-cost call to confirm the configured key is valid."""
    key = os.environ.get(API_KEY_ENV_VAR)
    if not key:
        return False, "No API key configured."

    try:
        client = Anthropic(api_key=key)
        client.models.list(limit=1)
        return True, "Connected to the Anthropic API."
    except AuthenticationError:
        return False, "The Anthropic API rejected this key — check that it was copied correctly."
    except Exception as exc:  # noqa: BLE001 — surface as a plain-English status (UR-003)
        return False, f"Could not reach the Anthropic API: {exc}"

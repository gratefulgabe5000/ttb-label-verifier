"""Shared FastAPI dependencies (WBS 3.3 — current-agent JWT validation)."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from db import get_db
from models.agent import Agent
from services.auth_service import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_agent(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Agent:
    if credentials is None:
        raise _credentials_exception

    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise _credentials_exception

    username = payload.get("sub")
    if username is None:
        raise _credentials_exception

    agent = db.query(Agent).filter(Agent.username == username).first()
    if agent is None:
        raise _credentials_exception

    return agent

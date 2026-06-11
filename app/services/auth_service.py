"""Password hashing and JWT issuance/validation (WBS 3.0, SR-001/SR-002)."""

from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import get_settings
from models.agent import Agent

settings = get_settings()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def authenticate_agent(db: Session, username: str, password: str) -> Agent | None:
    agent = db.query(Agent).filter(Agent.username == username).first()
    if agent is None or not verify_password(password, agent.password_hash):
        return None
    return agent


def create_access_token(agent: Agent, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    payload = {
        "sub": agent.username,
        "agent_id": agent.id,
        "display_name": agent.display_name,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Raises jose.JWTError (incl. ExpiredSignatureError) if invalid/expired."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

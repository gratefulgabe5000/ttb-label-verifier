"""Seed initial agent accounts (WBS 3.1, SR-001).

Idempotent — safe to re-run; existing usernames are skipped.

Usage:
    .venv/Scripts/python.exe seed.py
"""

from db import SessionLocal, init_db
from models.agent import Agent
from services.auth_service import hash_password

# Demo credentials — also documented in .env.example / README "First Run".
SEED_AGENTS = [
    {"username": "agent1", "display_name": "Agent One", "password": "password123"},
    {"username": "agent2", "display_name": "Agent Two", "password": "password123"},
]


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        for seed in SEED_AGENTS:
            if db.query(Agent).filter(Agent.username == seed["username"]).first():
                print(f"Agent '{seed['username']}' already exists, skipping.")
                continue

            db.add(
                Agent(
                    username=seed["username"],
                    display_name=seed["display_name"],
                    password_hash=hash_password(seed["password"]),
                )
            )
            print(f"Created agent '{seed['username']}'.")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()

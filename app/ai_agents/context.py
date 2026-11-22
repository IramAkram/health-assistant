from dataclasses import dataclass

from sqlalchemy.orm import Session


@dataclass
class AgentContext:
    """Passed to every tool call. user_id comes from the authenticated JWT, never from the LLM."""
    db: Session
    user_id: int

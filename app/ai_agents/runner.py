import logging

from sqlalchemy.orm import Session

from ..config import settings
from .fallback import run_demo

log = logging.getLogger(__name__)

DISCLAIMER = "\n\nNote: this is general wellness information, not medical advice or a diagnosis."


async def run_assistant(db: Session, user_id: int, message: str) -> tuple[str, str]:
    """Returns (reply, mode). Uses OpenAI Agents SDK when a key is set, otherwise offline demo mode."""
    if settings.OPENAI_API_KEY:
        try:
            from agents import Runner

            from .context import AgentContext
            from .specialists import build_coordinator

            result = await Runner.run(build_coordinator(), message,
                                      context=AgentContext(db=db, user_id=user_id), max_turns=8)
            return str(result.final_output) + DISCLAIMER, "agents"
        except Exception as exc:  # network / quota / SDK problems -> graceful fallback
            log.warning("Agents SDK failed (%s); using demo mode.", exc)
    return run_demo(db, user_id, message) + DISCLAIMER, "demo"

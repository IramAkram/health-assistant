from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..ai_agents.runner import run_assistant
from ..deps import get_current_user, get_db
from ..models import User
from ..schemas import ChatRequest, ChatResponse
from ..services.activity import log_activity

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.post("/chat", response_model=ChatResponse)
async def chat(data: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reply, mode = await run_assistant(db, user.id, data.message)
    log_activity(db, user.id, "used assistant")
    return ChatResponse(reply=reply, mode=mode)

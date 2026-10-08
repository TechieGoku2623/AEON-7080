"""AI Scientist and data analyst endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from aeon_api.db import get_session
from aeon_api.models import AIConversation, AIPlan, ToolExecution, Workspace
from aeon_api.security import current_workspace, new_id
from ai_scientist.orchestrator.orchestrator import answer_question
from ai_scientist.planner.planner import plan_question
from ai_scientist.researcher.researcher import retrieve

router = APIRouter(prefix="/api/ai", tags=["ai"])


class ChatRequest(BaseModel):
    message: str
    execute: bool = False
    config: dict | None = None


@router.post("/plan")
def plan(body: ChatRequest, workspace: Workspace = Depends(current_workspace), session: Session = Depends(get_session)) -> dict:
    planned = plan_question(body.message)
    record = AIPlan(id=new_id(), workspace_id=workspace.id, plan_json=planned)
    session.add(record)
    session.add(AIConversation(id=new_id(), workspace_id=workspace.id, role="user", content=body.message))
    session.commit()
    return {"plan_id": record.id, "plan": planned}


@router.post("/execute")
def execute(body: ChatRequest, workspace: Workspace = Depends(current_workspace), session: Session = Depends(get_session)) -> dict:
    planned = plan_question(body.message)
    plan_row = AIPlan(id=new_id(), workspace_id=workspace.id, plan_json=planned)
    session.add(plan_row)
    response = answer_question(body.message, body.config)
    for tool in (response.get("result") or {}).get("tools", []):
        session.add(
            ToolExecution(
                id=new_id(),
                plan_id=plan_row.id,
                tool_name=tool["name"],
                args_json={"question": body.message},
                result_summary_json={"status": tool["status"]},
            )
        )
    session.add(
        AIConversation(
            id=new_id(),
            workspace_id=workspace.id,
            role="scientist",
            content=(response.get("result") or {}).get("explanation") or planned.get("reason") or "",
        )
    )
    session.commit()
    return response


@router.post("/chat")
def chat(body: ChatRequest, workspace: Workspace = Depends(current_workspace), session: Session = Depends(get_session)) -> dict:
    if body.execute:
        return execute(body, workspace, session)
    return plan(body, workspace, session)


@router.post("/analyze")
def analyze(body: ChatRequest, workspace: Workspace = Depends(current_workspace)) -> dict:
    """Interpret an already computed explanation. Does not create new numbers."""

    return {
        "explanation": body.message,
        "references": retrieve(body.message, external_enabled=False),
        "note": "Analyze echoes the supplied text and does not compute a new result. Run execute for numbers.",
    }

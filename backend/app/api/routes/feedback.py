"""Feedback routes."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.api.deps import ActiveUser, DbSession
from app.schemas.report import FeedbackCreate, FeedbackRead
from app.services.feedback_service import FeedbackService

router = APIRouter(tags=["feedback"])


@router.post(
    "",
    response_model=FeedbackRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback on a message",
)
async def create_feedback(
    payload: FeedbackCreate,
    db: DbSession,
    user: ActiveUser,
) -> FeedbackRead:
    """Record the current user's feedback on an assistant message."""
    fb = await FeedbackService(db).create(payload, user.id)
    return FeedbackRead.model_validate(fb)


@router.get("", response_model=list[FeedbackRead], summary="List message feedback")
async def list_feedback(
    db: DbSession,
    _user: ActiveUser,
    message_id: str = Query(...),
) -> list[FeedbackRead]:
    """List all feedback recorded for a message."""
    items = await FeedbackService(db).list_for_message(message_id)
    return [FeedbackRead.model_validate(f) for f in items]

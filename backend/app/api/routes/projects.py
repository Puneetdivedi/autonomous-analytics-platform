"""Project CRUD routes."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import ActiveUser, DbSession
from app.schemas.common import Message
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(tags=["projects"])


@router.get("", response_model=list[ProjectRead], summary="List projects")
async def list_projects(db: DbSession, user: ActiveUser) -> list[ProjectRead]:
    """List projects owned by the current user (all projects for admins)."""
    projects = await ProjectService(db).list_for_user(user)
    return [ProjectRead.model_validate(p) for p in projects]


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project",
)
async def create_project(
    payload: ProjectCreate, db: DbSession, user: ActiveUser
) -> ProjectRead:
    """Create a new project owned by the current user."""
    project = await ProjectService(db).create(payload, user)
    return ProjectRead.model_validate(project)


@router.get("/{project_id}", response_model=ProjectRead, summary="Get a project")
async def get_project(
    project_id: str, db: DbSession, user: ActiveUser
) -> ProjectRead:
    """Fetch a single project the user can access."""
    project = await ProjectService(db).get(project_id, user)
    return ProjectRead.model_validate(project)


@router.patch(
    "/{project_id}", response_model=ProjectRead, summary="Update a project"
)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    db: DbSession,
    user: ActiveUser,
) -> ProjectRead:
    """Update a project the user can access."""
    project = await ProjectService(db).update(project_id, payload, user)
    return ProjectRead.model_validate(project)


@router.delete(
    "/{project_id}", response_model=Message, summary="Delete a project"
)
async def delete_project(
    project_id: str, db: DbSession, user: ActiveUser
) -> Message:
    """Delete a project the user can access."""
    await ProjectService(db).delete(project_id, user)
    return Message(detail="Project deleted")

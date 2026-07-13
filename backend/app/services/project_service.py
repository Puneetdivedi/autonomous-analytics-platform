"""Project service — owner-scoped CRUD."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError
from app.models.project import Project
from app.models.user import User
from app.repositories.project_repo import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """CRUD for projects, scoped to the owning user (admins bypass scope)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.projects = ProjectRepository(session)

    @staticmethod
    def _is_admin(user: User) -> bool:
        return user.is_superuser or user.role.value == "admin"

    def _assert_can_access(self, project: Project, user: User) -> None:
        if project.owner_id != user.id and not self._is_admin(user):
            raise AuthorizationError("You do not have access to this project")

    async def list_for_user(self, user: User) -> list[Project]:
        """List projects visible to ``user`` (own projects, or all for admin)."""
        if self._is_admin(user):
            return await self.projects.list(order_by=Project.created_at.desc())
        return await self.projects.list_for_owner(user.id)

    async def get(self, project_id: str, user: User) -> Project:
        """Return a project after verifying access."""
        project = await self.projects.get_or_404(project_id)
        self._assert_can_access(project, user)
        return project

    async def create(self, data: ProjectCreate, user: User) -> Project:
        """Create a project owned by ``user``."""
        return await self.projects.create(
            name=data.name,
            description=data.description,
            owner_id=user.id,
        )

    async def update(self, project_id: str, data: ProjectUpdate, user: User) -> Project:
        """Update a project after verifying access."""
        project = await self.get(project_id, user)
        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return project
        return await self.projects.update(project, **changes)

    async def delete(self, project_id: str, user: User) -> None:
        """Delete a project after verifying access."""
        project = await self.get(project_id, user)
        await self.projects.delete(project)

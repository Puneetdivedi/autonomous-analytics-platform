"""Idempotent database seeding.

Creates a default administrator account and a sample project if they do not
already exist. Safe to run repeatedly (e.g. on container start).

Run directly with:  ``python -m app.database.seed``
"""

from __future__ import annotations

import asyncio

from app.core.logging import configure_logging, get_logger
from app.core.security import hash_password
from app.database.session import AsyncSessionLocal
from app.models.enums import UserRole
from app.repositories.project_repo import ProjectRepository
from app.repositories.user_repo import UserRepository

logger = get_logger(__name__)

ADMIN_EMAIL = "admin@eaap.local"
ADMIN_PASSWORD = "Admin123!"  # noqa: S105 — dev seed credential
SAMPLE_PROJECT_NAME = "Sample Project"


async def seed() -> None:
    """Create the default admin user and a sample project if absent."""
    async with AsyncSessionLocal() as session:
        users = UserRepository(session)
        projects = ProjectRepository(session)

        admin = await users.get_by_email(ADMIN_EMAIL)
        if admin is None:
            admin = await users.create(
                email=ADMIN_EMAIL,
                full_name="Platform Administrator",
                hashed_password=hash_password(ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                is_active=True,
                is_superuser=True,
            )
            logger.info("seed.admin_created", email=ADMIN_EMAIL)
        else:
            logger.info("seed.admin_exists", email=ADMIN_EMAIL)

        existing = await projects.list_for_owner(admin.id)
        if not any(p.name == SAMPLE_PROJECT_NAME for p in existing):
            await projects.create(
                name=SAMPLE_PROJECT_NAME,
                description="A sample project created by the seed script.",
                owner_id=admin.id,
            )
            logger.info("seed.sample_project_created")
        else:
            logger.info("seed.sample_project_exists")

        await session.commit()


if __name__ == "__main__":
    configure_logging()
    asyncio.run(seed())

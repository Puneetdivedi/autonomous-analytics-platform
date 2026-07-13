"""Generic async repository base class."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Async CRUD helper bound to a single ORM model.

    Subclasses set :attr:`model` and may add query methods specific to their
    entity. All methods use SQLAlchemy 2.0 style ``select`` statements.
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id: Any) -> ModelT | None:
        """Return the row by primary key or ``None``."""
        return await self.session.get(self.model, id)

    async def get_or_404(self, id: Any) -> ModelT:
        """Return the row by primary key or raise :class:`NotFoundError`."""
        obj = await self.get(id)
        if obj is None:
            raise NotFoundError(
                f"{self.model.__name__} not found",
                details={"id": str(id)},
            )
        return obj

    async def list(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
        order_by: Any | None = None,
        **filters: Any,
    ) -> list[ModelT]:
        """Return rows matching the given equality filters."""
        stmt = select(self.model)
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, **filters: Any) -> int:
        """Return the number of rows matching the given equality filters."""
        stmt = select(func.count()).select_from(self.model)
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def create(self, **data: Any) -> ModelT:
        """Insert and flush a new row, returning the persisted instance."""
        obj = self.model(**data)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ModelT, **data: Any) -> ModelT:
        """Apply attribute updates to ``obj`` and flush."""
        for field, value in data.items():
            setattr(obj, field, value)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: ModelT) -> None:
        """Delete ``obj`` and flush."""
        await self.session.delete(obj)
        await self.session.flush()

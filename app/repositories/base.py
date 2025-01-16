from functools import reduce
from typing import Any, Generic, Type, TypeVar

from sqlalchemy import Select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy.sql.expression import select

from app.core.database.session import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db_session: AsyncSession):
        self.session = db_session
        self.model_class: Type[ModelType] = model

    async def edit_model(
        self, model: ModelType, update_data: dict[str, Any]
    ) -> ModelType:
        for key, value in update_data.items():
            setattr(model, key, value)
        return model

    async def create(self, attributes: dict[str, Any]) -> ModelType:
        if attributes is None:
            attributes = {}
        model = self.model_class(**attributes)
        self.session.add(model)
        return model

    async def get_all(
        self, skip: int = 0, limit: int = 100, join_: set[str] | None = None
    ) -> list[ModelType]:
        query = await self._query(join_)
        query = query.offset(skip).limit(limit)

        return await self._all(query)

    async def get_by_ids(
        self, ids: list[int], join_: set[str] | None = None
    ) -> list[ModelType]:
        query = await self._query(join_)
        query = query.filter(self.model_class.id.in_(ids))

        return await self._all(query)

    async def get_by_column(
        self,
        column: str,
        value: Any,
        join_: set[str] | None = None,
        unique: bool = False,
    ) -> ModelType:
        query = await self._query(join_)
        query = await self._get_by(query, column, value)

        if unique:
            return await self._one_or_none(query)

        return await self._all(query)

    async def delete(self, model: ModelType) -> None:
        await self.session.delete(model)

    async def delete_by_id(self, id: int) -> None:
        query = delete(self.model_class).where(self.model_class.id == id)
        await self.session.execute(query)

    async def _query(
        self,
        join_: set[str] | None = None,
        order_: dict | None = None,
    ) -> Select:
        query = select(self.model_class)
        query = await self._maybe_join(query, join_)
        query = await self._maybe_ordered(query, order_)

        return query

    async def _all(self, query: Select) -> list[ModelType]:
        query = await self.session.execute(query)
        return query.unique().scalars().all()

    async def _first(self, query: Select) -> ModelType | None:
        query = await self.session.scalars(query)
        return query.first()

    async def _one_or_none(self, query: Select) -> ModelType | None:
        query = await self.session.scalars(query)
        query = query.unique()
        return query.one_or_none()

    async def _count(self, query: Select) -> int:
        query = query.subquery()
        query = await self.session.scalars(select(func.count()).select_from(query))
        return query.one()

    async def _sort_by(
        self,
        query: Select,
        sort_by: str,
        order: str | None = "asc",
        model: Type[ModelType] | None = None,
        case_insensitive: bool = False,
    ) -> Select:
        model = model or self.model_class

        order_column = None

        if case_insensitive:
            order_column = func.lower(getattr(model, sort_by))
        else:
            order_column = getattr(model, sort_by)

        if order == "desc":
            return query.order_by(order_column.desc())

        return query.order_by(order_column.asc())

    async def _get_by(self, query: Select, field: str, value: Any) -> Select:
        return query.where(getattr(self.model_class, field) == value)

    async def _maybe_join(self, query: Select, join_: set[str] | None = None) -> Select:
        if not join_:
            return query

        if not isinstance(join_, set):
            raise TypeError("join_ must be a set")

        return reduce(self._add_join_to_query, join_, query)

    async def _maybe_ordered(self, query: Select, order_: dict | None = None) -> Select:
        if order_:
            if order_["asc"]:
                for order in order_["asc"]:
                    query = query.order_by(getattr(self.model_class, order).asc())
            else:
                for order in order_["desc"]:
                    query = query.order_by(getattr(self.model_class, order).desc())

        return query

    def _add_join_to_query(self, query: Select, join_: set[str]) -> Select:
        return getattr(self, "_join_" + join_)(query)

    async def execute(self, query: str, params: dict = None):
        try:
            result = await self.session.execute(text(query), params)
            await self.session.commit()
            rows = result.fetchall()
            return [row._asdict() for row in rows]
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f"Error executing query: {e}")

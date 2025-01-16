from typing import Any, Generic, Type, TypeVar

from app.core.database.session import Base
from app.core.exceptions import NotFoundException
from app.repositories.base import BaseRepository

ModelType = TypeVar("ModelType", bound=Base)


class BaseController(Generic[ModelType]):
    """Base class for data controllers."""

    def __init__(self, model: Type[ModelType], repository: BaseRepository) -> None:
        self.model_class: type[ModelType] = model
        self.repository: BaseRepository[Any] = repository

    async def get_by_id(self, id_: int, join_: set[str] | None = None) -> ModelType:
        db_obj = await self.repository.get_by_column(
            column="id", value=id_, join_=join_, unique=True
        )
        if not db_obj:
            raise NotFoundException(
                f"{self.model_class.__tablename__.title()} with id: {id_} does not exist"
            )

        return db_obj

    async def get_by_ids(self, ids_: list[int]) -> list[ModelType]:
        db_objs: list[Any] = await self.repository.get_by_ids(ids=ids_)
        return db_objs

    async def get_by_column(
        self,
        column: str,
        value: Any,
        join_: set[str] | None = None,
        unique: bool = False,
    ) -> list[ModelType]:
        response = await self.repository.get_by_column(
            column=column, value=value, join_=join_, unique=unique
        )
        return response

    async def get_all(
        self, skip: int = 0, limit: int = 100, join_: set[str] | None = None
    ) -> list[ModelType]:

        response: list[Any] = await self.repository.get_all(skip, limit, join_)
        return response

    async def create(self, attributes: dict[str, Any]) -> ModelType:
        create = await self.repository.create(attributes)
        await self.repository.session.commit()
        return create

    async def delete_by_id(self, id: int) -> None:
        await self.repository.delete_by_id(id)
        await self.repository.session.commit()

    async def sort_by_column(
        self,
        column: str,
        join_: set[str] | None = None,
        order: str | None = "asc",
    ) -> list[ModelType]:
        query = await self.repository._query()
        query = await self.repository._sort_by(query=query, sort_by=column, order=order)
        response: list[Any] = await self.repository._all(query)
        return response

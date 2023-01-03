from dataclasses import dataclass

from src.application.base.query import Query, QueryHandler
from src.application.user import dto
from src.application.user.interfaces.persistence import UserReader
from src.domain.user.value_objects import Username


@dataclass(frozen=True)
class GetUserByUsername(Query[dto.User]):
    username: Username


class GetUserByUsernameHandler(QueryHandler[GetUserByUsername, dto.User]):
    def __init__(self, user_reader: UserReader) -> None:
        self._user_reader = user_reader

    async def __call__(self, query: GetUserByUsername) -> dto.User:
        user = await self._user_reader.get_user_by_username(query.username)
        return user
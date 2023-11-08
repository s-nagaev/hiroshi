from abc import ABC, abstractmethod

from hiroshi.models import Message, User


class Database(ABC):
    @abstractmethod
    async def get_or_create_user(self, user_id: int) -> User:
        ...

    @abstractmethod
    async def save_user(self, user: User) -> None:
        ...

    @abstractmethod
    async def add_message(self, user: User, message: Message, ttl: int | None = None) -> None:
        ...

    @abstractmethod
    async def get_messages(self, user: User) -> list[dict[str, str]]:
        ...

    @abstractmethod
    async def drop_messages(self, user: User) -> None:
        ...

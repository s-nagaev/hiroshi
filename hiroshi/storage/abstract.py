from abc import ABC, abstractmethod

from hiroshi.models import Chat, Message


class Database(ABC):
    @abstractmethod
    async def get_or_create_chat(self, chat_id: int) -> Chat:
        ...

    @abstractmethod
    async def save_chat(self, chat: Chat) -> None:
        ...

    @abstractmethod
    async def add_message(self, chat: Chat, message: Message, ttl: int | None = None) -> None:
        ...

    @abstractmethod
    async def get_messages(self, chat: Chat) -> list[dict[str, str]]:
        ...

    @abstractmethod
    async def drop_messages(self, chat: Chat) -> None:
        ...

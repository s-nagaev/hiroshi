from urllib.parse import urlparse

from loguru import logger
from redis.asyncio import Redis, from_url

from hiroshi.config import gpt_settings
from hiroshi.models import Chat, Message
from hiroshi.storage.abstract import Database


class RedisStorage(Database):
    def __init__(self, url: str, password: str | None = None, db: int = 1) -> None:
        self.redis: Redis
        self.url = url
        self.password = password
        self.db = db
        logger.info("Redis storage initialized.")

    @classmethod
    async def create(cls, url: str, password: str | None = None, db: int = 1) -> "RedisStorage":
        instance = cls(url, password, db)
        await instance.connect()
        return instance

    async def connect(self) -> None:
        redis_dsn = self._combine_redis_dsn(base_dsn=self.url, password=self.password)
        self.redis = await from_url(redis_dsn)

    def _combine_redis_dsn(self, base_dsn: str, password: str | None) -> str:
        if not password:
            return base_dsn

        parsed_dsn = urlparse(base_dsn)
        password_in_dsn = parsed_dsn.password or None

        if password_in_dsn:
            logger.warning(
                "Redis password specified twice: in the REDIS_PASSWORD and REDIS environment variables. "
                "Trying to use the password from the Redis DSN..."
            )
            return base_dsn

        if host := parsed_dsn.hostname:
            return base_dsn.replace(host, f":{password}@{host}")

        raise ValueError("Incorrect Redis DSN string provided.")

    async def save_chat(self, chat: Chat) -> None:
        chat_key = f"chat:{chat.id}"
        chat_data = chat.json()
        await self.redis.set(chat_key, chat_data)

        for message in chat.messages:
            message_key = f"chat:{chat.id}:message:{message.id}"
            message_data = message.json()
            await self.redis.set(message_key, message_data)
            await self.redis.expire(message_key, gpt_settings.messages_ttl)

    async def create_chat(self, chat_id: int) -> Chat:
        chat = Chat(id=chat_id)
        initial_message = Message(role="system", content=gpt_settings.assistant_prompt)
        chat.messages.append(initial_message)
        chat_key = f"chat:{chat_id}"

        await self.redis.set(chat_key, chat.json())
        await self.add_message(chat=chat, message=initial_message)
        return chat

    async def get_chat(self, chat_id: int) -> Chat | None:
        chat_key = f"chat:{chat_id}"
        chat_data = await self.redis.get(chat_key)
        if not chat_data:
            return None

        chat = Chat.parse_raw(chat_data)
        message_keys_pattern = f"chat:{chat.id}:message:*"
        message_keys = await self.redis.keys(message_keys_pattern)
        chat_messages = [Message.parse_raw(await self.redis.get(message_key)) for message_key in message_keys]

        chat.messages = sorted(chat_messages, key=lambda msg: msg.id)

        return chat

    async def get_or_create_chat(self, chat_id: int) -> Chat:
        if chat := await self.get_chat(chat_id=chat_id):
            return chat
        return await self.create_chat(chat_id=chat_id)

    async def add_message(self, chat: Chat, message: Message, ttl: int | None = None) -> None:
        message_to_save = Message(role=message.role, content=message.content)
        message_key = f"chat:{chat.id}:message:{message.id}"

        await self.redis.set(name=message_key, value=message_to_save.json(exclude={"expire_at"}))
        if ttl:
            await self.redis.expire(name=message_key, time=ttl)

    async def get_messages(self, chat: Chat) -> list[dict[str, str]]:
        chat_refreshed = await self.get_or_create_chat(chat_id=chat.id)
        return [msg.dict(exclude={"expire_at", "id"}) for msg in chat_refreshed.messages]

    async def drop_messages(self, chat: Chat) -> None:
        message_keys_pattern = f"chat:{chat.id}:message:*"
        message_keys = await self.redis.keys(message_keys_pattern)

        for message_key in message_keys:
            await self.redis.delete(message_key)

        initial_message = Message(role="system", content=gpt_settings.assistant_prompt)
        chat.messages.append(initial_message)
        await self.add_message(chat=chat, message=initial_message, ttl=gpt_settings.messages_ttl)

    async def close(self) -> None:
        await self.redis.close()

import os
import pickle
import time
from typing import cast

from loguru import logger

from hiroshi.config import gpt_settings
from hiroshi.models import Chat, Message
from hiroshi.storage.abstract import Database


class LocalStorage(Database):
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        logger.info("Local storage initialized.")

    def _get_storage_filename(self, chat_id: int) -> str:
        return os.path.join(self.storage_path, f"{chat_id}.pkl")

    async def save_chat(self, chat: Chat) -> None:
        filename = self._get_storage_filename(chat.id)
        with open(filename, "wb") as f:
            pickle.dump(chat, f)

    async def create_chat(self, chat_id: int) -> Chat:
        chat = Chat(id=chat_id)
        initial_message = Message(role="system", content=gpt_settings.assistant_prompt)
        chat.messages = [
            initial_message,
        ]
        await self.save_chat(chat=chat)
        return chat

    async def get_chat(self, chat_id: int) -> Chat | None:
        filename = self._get_storage_filename(chat_id)
        try:
            if os.path.exists(filename):
                with open(filename, "rb") as f:
                    return cast(Chat, pickle.load(f))
        except Exception as e:
            logger.error(f"Couldn't get history for the chat {chat_id} due to exception: {str(e)[:240]}")
        return None

    async def get_or_create_chat(self, chat_id: int) -> Chat:
        if chat := await self.get_chat(chat_id=chat_id):
            return chat
        return await self.create_chat(chat_id=chat_id)

    async def add_message(self, chat: Chat, message: Message, ttl: int | None = None) -> None:
        user_refreshed = await self.get_or_create_chat(chat_id=chat.id)
        if ttl:
            expire_at = time.time() + ttl
        else:
            expire_at = None

        message_with_ttl = Message(role=message.role, content=message.content, expire_at=expire_at)
        user_refreshed.messages.append(message_with_ttl)
        await self.save_chat(user_refreshed)

    async def get_messages(self, chat: Chat) -> list[dict[str, str]]:
        user_refreshed = await self.get_or_create_chat(chat_id=chat.id)
        current_time = time.time()

        msgs = [
            msg.dict(exclude={"expire_at", "id"})
            for msg in user_refreshed.messages
            if msg.expire_at is None or msg.expire_at > current_time
        ]
        return msgs

    async def drop_messages(self, chat: Chat) -> None:
        initial_message = Message(role="system", content=gpt_settings.assistant_prompt)
        chat.messages = [
            initial_message,
        ]
        await self.save_chat(chat=chat)

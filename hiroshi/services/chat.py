from loguru import logger

from hiroshi.config import gpt_settings
from hiroshi.models import Message
from hiroshi.services.gpt import MODELS_AND_PROVIDERS, get_chat_response
from hiroshi.storage.abstract import Database
from hiroshi.storage.database import inject_database


@inject_database
async def set_active_provider(db: Database, chat_id: int, provider_selected: str) -> None:
    model_name, provider_name = MODELS_AND_PROVIDERS.get(provider_selected, ("gpt_35_long", "Default"))
    chat = await db.get_or_create_chat(chat_id=chat_id)
    chat.provider_name = provider_name if provider_name != "Default" else None
    chat.model_name = model_name
    await db.save_chat(chat)


@inject_database
async def reset_chat_history(db: Database, chat_id: int) -> None:
    chat = await db.get_or_create_chat(chat_id=chat_id)
    await db.drop_messages(chat=chat)


@inject_database
async def summarize(db: Database, chat_id: int) -> None:
    chat = await db.get_or_create_chat(chat_id=chat_id)

    chat_history = await db.get_messages(chat=chat)
    query_messages = [
        {
            "role": "assistant",
            "content": "Summarize this conversation in 700 characters or less",
        },
        {"role": "user", "content": str(chat_history)},
    ]
    answer = await get_chat_response(messages=query_messages, provider=chat.provider, model=chat.model)
    if not answer:
        logger.warning(f"Could not summarize history for chat {chat_id}: empty response received from the Provider.")
        return None
    answer_message = Message(role="assistant", content=answer)
    await reset_chat_history(chat_id=chat_id)
    await db.add_message(chat=chat, message=answer_message, ttl=gpt_settings.messages_ttl)


@inject_database
async def get_gtp_chat_answer(db: Database, chat_id: int, prompt: str) -> str | None:
    chat = await db.get_or_create_chat(chat_id=chat_id)
    query_message = Message(role="user", content=prompt)
    await db.add_message(chat=chat, message=query_message, ttl=gpt_settings.messages_ttl)
    conversation_messages = await db.get_messages(chat=chat)
    if answer := await get_chat_response(messages=conversation_messages, provider=chat.provider, model=chat.model):
        answer_message = Message(role="assistant", content=answer)
        await db.add_message(chat=chat, message=answer_message, ttl=gpt_settings.messages_ttl)
        return answer
    return None


@inject_database
async def check_history_and_summarize(db: Database, chat_id: int) -> bool:
    chat = await db.get_or_create_chat(chat_id=chat_id)

    # Roughly estimating how many tokens the current conversation history will comprise. It is possible to calculate
    # this accurately, but the modules that can be used for this need to be separately built for armv7, which is
    # difficult to do right now (but will be done further, I hope).
    if len(str(chat.messages)) / 4 >= gpt_settings.max_history_tokens:
        await summarize(chat_id=chat_id)
        return True
    return False

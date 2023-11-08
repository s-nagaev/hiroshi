from loguru import logger

from hiroshi.config import gpt_settings
from hiroshi.models import Message
from hiroshi.services.gpt import MODELS_AND_PROVIDERS, get_chat_response
from hiroshi.storage.abc import Database
from hiroshi.storage.database import inject_database


@inject_database
async def set_active_provider(db: Database, user_id: int, provider_selected: str) -> None:
    model_name, provider_name = MODELS_AND_PROVIDERS.get(provider_selected, ("gpt_35_long", "Default"))
    user = await db.get_or_create_user(user_id=user_id)
    user.provider_name = provider_name if provider_name != "Default" else None
    user.model_name = model_name
    await db.save_user(user)


@inject_database
async def reset_chat_history(db: Database, user_id: int) -> None:
    user = await db.get_or_create_user(user_id=user_id)
    await db.drop_messages(user=user)


@inject_database
async def summarize(db: Database, user_id: int) -> None:
    user = await db.get_or_create_user(user_id=user_id)

    chat_history = await db.get_messages(user=user)
    query_messages = [
        {
            "role": "assistant",
            "content": "Summarize this conversation in 700 characters or less",
        },
        {"role": "user", "content": str(chat_history)},
    ]
    answer = await get_chat_response(messages=query_messages, provider=user.provider, model=user.model)
    if not answer:
        logger.warning(f"Could not summarize history for user {user_id}: empty response received from the Provider.")
        return None
    answer_message = Message(role="assistant", content=answer)
    await reset_chat_history(user_id=user_id)
    await db.add_message(user=user, message=answer_message, ttl=gpt_settings.messages_ttl)


@inject_database
async def get_gtp_chat_answer(db: Database, user_id: int, prompt: str) -> str | None:
    user = await db.get_or_create_user(user_id=user_id)
    query_message = Message(role="user", content=prompt)
    await db.add_message(user=user, message=query_message, ttl=gpt_settings.messages_ttl)
    conversation_messages = await db.get_messages(user=user)
    if answer := await get_chat_response(messages=conversation_messages, provider=user.provider, model=user.model):
        answer_message = Message(role="assistant", content=answer)
        await db.add_message(user=user, message=answer_message, ttl=gpt_settings.messages_ttl)
        return answer
    return None


@inject_database
async def check_history_and_summarize(db: Database, user_id: int) -> bool:
    user = await db.get_or_create_user(user_id=user_id)

    # Roughly estimating how many tokens the current conversation history will comprise. It is possible to calculate
    # this accurately, but the modules that can be used for this need to be separately built for armv7, which is
    # difficult to do right now (but will be done further, I hope).
    if len(str(user.messages)) / 4 >= gpt_settings.max_history_tokens:
        await summarize(user_id=user_id)
        return True
    return False

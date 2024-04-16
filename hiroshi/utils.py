import io
from functools import wraps
from typing import Any, Callable

import httpx
from g4f.Provider import ProviderUtils
from loguru import logger
from telegram import Chat as TelegramChat
from telegram import Message as TelegramMessage
from telegram import Update
from telegram import User as TelegramUser
from telegram import constants
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from hiroshi.config import application_settings, gpt_settings, telegram_settings

GROUP_CHAT_TYPES = [constants.ChatType.GROUP, constants.ChatType.SUPERGROUP]
PERSONAL_CHAT_TYPES = [constants.ChatType.SENDER, constants.ChatType.PRIVATE]


def get_telegram_user(update: Update) -> TelegramUser:
    if user := update.effective_user:
        return user
    raise ValueError(f"Telegram incoming update does not contain valid user data. Update ID: {update.update_id}")


def get_telegram_chat(update: Update) -> TelegramChat:
    if chat := update.effective_chat:
        return chat
    raise ValueError(f"Telegram incoming update does not contain valid chat data. Update ID: {update.update_id}")


def get_telegram_message(update: Update) -> TelegramMessage:
    if message := update.effective_message:
        return message
    raise ValueError(f"Telegram incoming update does not contain valid message data. Update ID: {update.update_id}")


def get_prompt_with_replied_message(update: Update, initial_prompt: str) -> str:
    if not update.message or not update.message.reply_to_message:
        return initial_prompt

    user = get_telegram_user(update)
    if quoted_user := update.message.reply_to_message.from_user:
        quoted_user_name = quoted_user.name
    else:
        quoted_user_name = "user"

    quoted_message = update.message.reply_to_message.caption or update.message.reply_to_message.text
    prompt = f"> {quoted_message}\n>\n>  — *{quoted_user_name}*\n\n" f"{user.username}: {initial_prompt}"

    return prompt


async def send_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE, reply: bool = True, **kwargs: Any
) -> TelegramMessage:
    telegram_chat = get_telegram_chat(update=update)
    telegram_message = get_telegram_message(update=update)

    if reply:
        return await context.bot.send_message(
            chat_id=telegram_chat.id, reply_to_message_id=telegram_message.message_id, **kwargs
        )
    return await context.bot.send_message(chat_id=telegram_chat.id, **kwargs)


async def send_gpt_answer_message(gpt_answer: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_user = get_telegram_user(update=update)
    telegram_chat = get_telegram_chat(update=update)
    try:
        await send_message(update=update, context=context, text=gpt_answer, parse_mode=constants.ParseMode.MARKDOWN)
    except BadRequest as e:
        # Trying to handle an exception connected with markdown parsing: just re-sending the message in a text mode.
        logger.error(
            f"{telegram_user.name} got a Telegram Bad Request error while receiving GPT answer: {e}. "
            f"Trying to re-send it in plain text mode."
        )
        await send_message(update=update, context=context, text=gpt_answer)

        if "```" in gpt_answer:
            logger.info(
                f"{telegram_user.name} got and answer containing some code, but face with a markdown parse error. "
                f"Additionally sending answer as an attachment..."
            )
            file = io.BytesIO()
            file.write(gpt_answer.encode())
            file.seek(0)
            explain_message_text = (
                "Oops! 😯It looks like your answer contains some code, but Telegram can't display it properly. "
                "I'll additionally add your answer to the markdown file. 👇"
            )

            explain_message = await send_message(update=update, context=context, text=explain_message_text, reply=False)
            await context.bot.send_document(
                chat_id=telegram_chat.id,
                reply_to_message_id=explain_message.message_id,
                document=file,
                filename="answer.md",
            )


def user_is_allowed(tg_user: TelegramUser) -> bool:
    if not telegram_settings.users_whitelist:
        return True
    return any(identifier in telegram_settings.users_whitelist for identifier in (str(tg_user.id), tg_user.username))


def group_is_allowed(tg_chat: TelegramChat) -> bool:
    if not telegram_settings.groups_whitelist:
        return True
    return tg_chat.id in telegram_settings.groups_whitelist


def user_is_group_admin(tg_user: TelegramUser) -> bool:
    if not telegram_settings.group_admins:
        return True
    return any(identifier in telegram_settings.group_admins for identifier in (str(tg_user.id), tg_user.username))


def user_interacts_with_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    telegram_message = get_telegram_message(update=update)
    prompt = telegram_message.text

    if not prompt:
        return False

    if context.bot.first_name in prompt or context.bot.username in prompt:
        return True

    reply_message = telegram_message.reply_to_message
    if not reply_message or not reply_message.from_user:
        return False

    return reply_message.from_user.id == context.bot.id


def check_user_allow_to_apply_settings(func: Callable[..., Any]) -> Callable[..., Any]:
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        update: Update = kwargs.get("update") or args[1]
        context: ContextTypes.DEFAULT_TYPE = kwargs.get("context") or args[2]
        telegram_chat = get_telegram_chat(update=update)
        telegram_user = get_telegram_user(update=update)
        user_name = telegram_user.name or f"{telegram_user.first_name} ({telegram_user.id})"

        if telegram_chat.type in GROUP_CHAT_TYPES and not user_is_group_admin(tg_user=telegram_user):
            logger.warning(
                f"{user_name} (id={telegram_user.id}) is not allowed to set group settings (group {telegram_chat.id})"
            )
            await send_message(update=update, context=context, text="Ooops! You're not a group admin, sorry ( ._.)")
            return None

        return await func(*args, **kwargs)

    return wrapper


def check_user_allowance(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator controlling access to the chatbot.

    This deco checks:
        - if the specific user is allowed to interact with the chatbot, using ALLOW_BOTS and USERS_WHITELIST;
        - if the chatbot is allowed to be in a specific group, using a GROUPS_WHITELIST.

    If the specific user is disallowed to interact with the chatbot, the corresponding message will be sent.
    If the chatbot is disallowed to be in a specific group, it will send the corresponding message
    and leave it immediately.

    Args:
        func: async function that may rise openai exception.

    Returns:
        Wrapper function object.
    """

    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        update: Update = kwargs.get("update") or args[1]
        context: ContextTypes.DEFAULT_TYPE = kwargs.get("context") or args[2]
        telegram_user = get_telegram_user(update=update)
        user_name = telegram_user.name or f"{telegram_user.first_name} ({telegram_user.id})"

        if telegram_user.is_bot and not telegram_settings.allow_bots:
            logger.warning(f"Bots are not allowed. {user_name}'s request ignored.")
            return None

        if update.inline_query:
            if not user_is_allowed(tg_user=telegram_user):
                logger.warning(f"{user_name} (id={telegram_user.id}) is not allowed to work with me. Inline ignored.")
                return None
            return await func(*args, **kwargs)

        telegram_chat = get_telegram_chat(update=update)

        if telegram_chat.type in PERSONAL_CHAT_TYPES and not user_is_allowed(tg_user=telegram_user):
            logger.warning(f"{user_name} (id={telegram_user.id}) is not allowed to work with me. Request rejected.")
            await send_message(update=update, context=context, text=telegram_settings.message_for_disallowed_users)
            return None

        if telegram_chat.type in GROUP_CHAT_TYPES and not group_is_allowed(tg_chat=telegram_chat):
            message = (
                f"The group {telegram_chat.effective_name} (id: {telegram_chat.id}, link: {telegram_chat.link}) "
                f"does not exist in the whitelist. Leaving it..."
            )
            logger.warning(message)
            await context.bot.send_message(chat_id=telegram_chat.id, text=message, disable_web_page_preview=True)
            await telegram_chat.leave()
            return None

        return await func(*args, **kwargs)

    return wrapper


def handle_gpt_exceptions(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator handling openai module's exceptions.

    If the specific exception occurred, handles it and sends the corresponding message.

    Args:
        func: async function that may rise openai exception.

    Returns:
        Wrapper function object.
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        update: Update = kwargs.get("update") or args[1]
        context: ContextTypes.DEFAULT_TYPE = kwargs.get("context") or args[2]
        telegram_user = get_telegram_user(update=update)
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"{telegram_user.name} got an error: {str(e)[:240]}")
            msg = (
                "I'm sorry, but there seems to be a little hiccup with your request at the moment 😥 Would you mind "
                "trying again later? Don't worry, I'll be here to assist you whenever you're ready! 😼"
            )
            await send_message(update=update, context=context, text=msg)
            return None

    return wrapper


def log_application_settings() -> None:
    storage = "<red>REDIS</red>" if application_settings.redis else "<blue>LOCAL</blue>"

    logger_info = "<red>DISABLED</red>."

    if application_settings.monitoring_url:
        logger_info = (
            f"<blue>ACTIVE</blue>."
            f"MONITORING_FREQUENCY_CALL=<blue>{application_settings.monitoring_frequency_call}</blue>."
            f"MONITORING_URL=<blue>{application_settings.monitoring_url}</blue>"
        )

    messages = (
        f"Application is initialized using {storage} storage.",
        f"Bot name is <blue>{telegram_settings.bot_name}</blue>",
        f"Initial assistant prompt: <blue>{gpt_settings.assistant_prompt}</blue>",
        f"Proxy is <blue>{telegram_settings.proxy or 'UNSET'}</blue>",
        f"Messages TTL: <blue>{gpt_settings.max_conversation_age_minutes} minutes</blue>",
        f"Maximum conversation history size: <blue>{gpt_settings.max_history_tokens}</blue> tokens",
        f"Users whitelist: <blue>{telegram_settings.users_whitelist or 'UNSET'}</blue>",
        f"Groups whitelist: <blue>{telegram_settings.groups_whitelist or 'UNSET'}</blue>",
        f"Groups admins: <blue>{telegram_settings.group_admins or 'UNSET'}</blue>",
        f"Uptime checker: {logger_info}",
    )
    for message in messages:
        logger.opt(colors=True).info(message)

    if application_settings.redis_password:
        logger.opt(colors=True).warning(
            "`REDIS_PASSWORD` environment variable is <red>deprecated</red>. Use `REDIS` instead, i.e. "
            "`redis://:password@localhost:6379/0`"
        )


async def run_monitoring(context: ContextTypes.DEFAULT_TYPE) -> None:
    if not application_settings.monitoring_url:
        return

    transport = httpx.AsyncHTTPTransport(
        retries=application_settings.monitoring_retry_calls, proxy=application_settings.monitoring_proxy
    )

    async with httpx.AsyncClient(transport=transport, proxy=application_settings.monitoring_proxy) as client:
        try:
            result = await client.get(application_settings.monitoring_url)
        except Exception as error:
            logger.error(f"Uptime Checker failed with an Exception: {error}")
            return
        if result.is_error:
            logger.error(f"Uptime Checker failed. status_code({result.status_code}) msg: {result.text}")


def is_provider_active(model_and_provider_names: tuple[str, str]) -> bool:
    _, provider_name = model_and_provider_names
    if provider := ProviderUtils.convert.get(provider_name):
        return bool(provider.working)
    return False

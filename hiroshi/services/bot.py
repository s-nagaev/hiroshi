import asyncio

from loguru import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, constants
from telegram.ext import ContextTypes

from hiroshi.config import application_settings, gpt_settings
from hiroshi.services.chat import (
    check_history_and_summarize,
    get_gtp_chat_answer,
    reset_chat_history,
    set_active_provider,
)
from hiroshi.services.gpt import retrieve_available_providers
from hiroshi.storage.abstract import Database
from hiroshi.storage.database import inject_database
from hiroshi.utils import (
    get_prompt_with_replied_message,
    get_telegram_chat,
    get_telegram_message,
    get_telegram_user,
    handle_gpt_exceptions,
    send_gpt_answer_message,
)


async def handle_provider_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    provider_selected = query.data
    telegram_user = get_telegram_user(update=update)
    telegram_chat = get_telegram_chat(update=update)
    await set_active_provider(chat_id=telegram_chat.id, provider_selected=provider_selected)
    logger.info(
        f"{telegram_user.name} (Telegram ID: {telegram_user.id}) in the {telegram_chat} "
        f"switched to provider: '{provider_selected}'"
    )
    await query.edit_message_text(text=f"Now you will work with the {query.data} service.")


@handle_gpt_exceptions
@inject_database
async def handle_prompt(db: Database, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_user = get_telegram_user(update=update)
    telegram_chat = get_telegram_chat(update=update)
    telegram_message = get_telegram_message(update=update)
    prompt = telegram_message.text
    hiroshi_user = await db.get_or_create_chat(chat_id=telegram_chat.id)

    if not prompt:
        return None

    if prompt.startswith("/ask"):
        prompt = prompt.replace("/ask", "", 1).strip()

    prompt_to_log = prompt.replace("\r", " ").replace("\n", " ")
    logger.info(
        f"{telegram_user.name} (Telegram ID: {telegram_user.id}) sent a new message in the "
        f"{telegram_chat.type.upper()} chat {telegram_chat.id}"
        f"{': ' + prompt_to_log if application_settings.log_prompt_data else ''}"
    )

    # Get replied message concatenated to the prompt.
    prompt = get_prompt_with_replied_message(update=update, prompt=prompt)

    get_gtp_chat_answer_task = asyncio.ensure_future(get_gtp_chat_answer(chat_id=telegram_chat.id, prompt=prompt))

    while not get_gtp_chat_answer_task.done():
        await context.bot.send_chat_action(chat_id=telegram_chat.id, action=constants.ChatAction.TYPING)
        await asyncio.sleep(2.5)

    gpt_answer = await get_gtp_chat_answer_task

    if not gpt_answer:
        logger.warning(
            f"{telegram_user.name} (Telegram ID: {telegram_user.id}) got an EMPTY response from the "
            f"{hiroshi_user.provider_name.upper() if hiroshi_user.provider_name else 'Default Provider'} "
            f"({hiroshi_user.model_name.upper()}) in the {telegram_chat.type.upper()} chat {telegram_chat.id}."
        )
        sorry_answer = (
            "Hey! Seems the remote GPT Provider didn't answer properly: an empty message was received. I've asked it "
            f"{gpt_settings.retries} times but didn't succeed. Please, try again a bit later or, maybe, switch "
            f"to another model/provider."
        )
        await send_gpt_answer_message(gpt_answer=sorry_answer, update=update, context=context)
        return None

    answer_to_log = gpt_answer.replace("\r", " ").replace("\n", " ")
    logged_answer = f"Answer: {answer_to_log}" if application_settings.log_prompt_data else ""

    logger.info(
        f"{telegram_user.name} (Telegram ID: {telegram_user.id}) got an answer from the "
        f"{hiroshi_user.provider_name.upper() if hiroshi_user.provider_name else 'Default Provider'} "
        f"({hiroshi_user.model_name.upper()}) in the {telegram_chat.type.upper()} chat {telegram_chat.id}. "
        f"{logged_answer}"
    )
    await send_gpt_answer_message(gpt_answer=gpt_answer, update=update, context=context)
    history_is_summarized = await check_history_and_summarize(chat_id=telegram_chat.id)
    if history_is_summarized:
        logger.info(f"{telegram_user.name} (Telegram ID: {telegram_user.id}) history successfully summarized.")


async def handle_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_chat = get_telegram_chat(update=update)
    telegram_user = get_telegram_user(update=update)
    logger.info(f"{telegram_user.name} (Telegram ID: {telegram_user.id}) conversation history reset.")

    await reset_chat_history(chat_id=telegram_chat.id)
    await context.bot.send_message(chat_id=telegram_chat.id, text="Done!")


async def handle_available_providers_options() -> InlineKeyboardMarkup:
    models_available = retrieve_available_providers()
    keyboard = [[InlineKeyboardButton(model.upper(), callback_data=model)] for model in models_available]
    return InlineKeyboardMarkup(keyboard)

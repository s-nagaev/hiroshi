import asyncio

import requests
from loguru import logger
from telegram import (
    BotCommand,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from hiroshi.config import application_settings, telegram_settings
from hiroshi.services.bot import (
    handle_available_providers_options,
    handle_prompt,
    handle_provider_selection,
    handle_reset,
)
from hiroshi.utils import (
    GROUP_CHAT_TYPES,
    check_user_allow_to_apply_settings,
    check_user_allowance,
    get_telegram_chat,
    get_telegram_message,
    log_application_settings,
    user_interacts_with_bot,
)


class HiroshiBot:
    def __init__(self) -> None:
        self.commands = [
            BotCommand(command="about", description="About this bot"),
            BotCommand(command="help", description="Show the help message"),
            BotCommand(
                command="ask",
                description=(
                    "Ask me any question (in group chat, for example) (e.g. /ask which program language is the best?)"
                ),
            ),
            BotCommand(
                command="reset", description="Reset your conversation history (will reduce prompt and save some tokens)"
            ),
            BotCommand(command="provider", description="Select GPT provider"),
        ]

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        telegram_message = get_telegram_message(update=update)
        commands = [f"/{command.command} - {command.description}" for command in self.commands]
        commands_desc = "\n".join(commands)
        help_text = (
            f"Hey! My name is {telegram_settings.bot_name}, and I'm your FREE GPT experience provider!\n\n"
            f"{commands_desc}"
        )
        await telegram_message.reply_text(help_text, disable_web_page_preview=True)

    async def about(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        telegram_message = get_telegram_message(update=update)

        text = (
            "If you like me, or you have some questions, feature requests or any issues found, please, "
            "feel free to visit my GitHub page: https://github.com/s-nagaev/hiroshi. Thank you!\n\n"
        )
        await telegram_message.reply_text(text, disable_web_page_preview=True)

    @check_user_allowance
    @check_user_allow_to_apply_settings
    async def reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        asyncio.create_task(handle_reset(update=update, context=context))

    @check_user_allowance
    async def prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        telegram_chat = get_telegram_chat(update=update)
        telegram_message = get_telegram_message(update=update)
        prompt = telegram_message.text

        if not prompt:
            return None

        if (
            telegram_chat.type in GROUP_CHAT_TYPES
            and telegram_settings.answer_direct_messages_only
            and "/ask" not in prompt
            and not user_interacts_with_bot(update=update, context=context)
        ):
            return None
        asyncio.create_task(handle_prompt(update=update, context=context))

    @check_user_allowance
    async def ask(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        asyncio.create_task(handle_prompt(update=update, context=context))

    @check_user_allowance
    @check_user_allow_to_apply_settings
    async def show_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        telegram_message = get_telegram_message(update=update)
        reply_markup = await handle_available_providers_options()

        await telegram_message.reply_text("Please, select GPT service provider:", reply_markup=reply_markup)

    @check_user_allow_to_apply_settings
    async def select_provider(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        asyncio.create_task(handle_provider_selection(update=update, context=context))

    @check_user_allowance
    async def inline_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        inline_query = update.inline_query
        if not inline_query:
            return
        query = inline_query.query
        results = [
            InlineQueryResultArticle(
                id=inline_query.id,
                title=f"Ask {telegram_settings.bot_name}",
                input_message_content=InputTextMessageContent(message_text=query),
                description=query,
                thumbnail_url="https://i.ibb.co/njjQMVQ/hiroshi_logo.png",
            )
        ]
        await inline_query.answer(results)

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.error(f"Error occurred while handling an update: {str(context.error)[:240]}")

    async def post_init(self, application: Application) -> None:  # type: ignore
        await application.bot.set_my_commands(self.commands)

    def run(self) -> None:
        if telegram_settings.proxy:
            app = (
                ApplicationBuilder()
                .token(telegram_settings.token)
                .proxy_url(telegram_settings.proxy)
                .get_updates_proxy_url(telegram_settings.proxy)
                .post_init(self.post_init)
                .build()
            )
        else:
            app = ApplicationBuilder().token(telegram_settings.token).post_init(self.post_init).build()

        if telegram_settings.show_about:
            app.add_handler(CommandHandler("about", self.about))
        app.add_handler(CommandHandler("help", self.help))
        app.add_handler(CommandHandler("reset", self.reset))
        app.add_handler(CommandHandler("start", self.help))
        app.add_handler(CommandHandler("ask", self.ask))
        app.add_handler(CommandHandler("provider", self.show_menu))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.prompt))
        app.add_handler(CallbackQueryHandler(self.select_provider))
        # TODO It doesn't work de-facto. Need to fix it first.
        # app.add_handler(
        #     InlineQueryHandler(
        #         self.inline_query,
        #         chat_types=[constants.ChatType.GROUP, constants.ChatType.SUPERGROUP],
        #     )
        # )
        app.add_error_handler(self.error_handler)
        app.run_polling()


async def uptime_checker() -> None:
    if application_settings.monitoring_is_active and application_settings.monitoring_url:
        logger.info(f'Uptime Checker started. '
                    f'MONITORING_FREQUENCY_CALL={application_settings.monitoring_frequency_call} '
                    f'MONITORING_URL={application_settings.monitoring_url}')
        while True:
            result = await asyncio.to_thread(requests.get, application_settings.monitoring_url)
            if result.status_code != 200:
                logger.error(f'Uptime Checker failed. status_code({result.status_code}) msg: {result.text}')
            # Converting from minutes to seconds.
            await asyncio.sleep(application_settings.monitoring_frequency_call * 60)
    else:
        logger.info('Uptime Checker disabled. To turn it on set MONITORING_IS_ACTIVE environment variable.')


if __name__ == "__main__":
    log_application_settings()
    telegram_bot = HiroshiBot()
    telegram_bot.run()
    asyncio.run(uptime_checker())

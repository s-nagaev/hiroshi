import g4f
from g4f.base_provider import BaseProvider
from g4f.models import Model
from loguru import logger

from hiroshi.config import gpt_settings

MODELS_AND_PROVIDERS: dict[str, tuple[str, str]] = {
    "Default": ("gpt_35_long", "Default"),
    "GPT-3.5 (The best/fastest provider)": ("gpt_35_long", "Default"),
    "GPT-4 (The best/fastest provider)": ("gpt_4", "Default"),
    "Bing (GPT-4)": ("gpt_4", "Bing"),
    "ChatBase (GPT-3.5)": ("gpt-3.5-turbo", "ChatBase"),
    "ChatgptAi (GPT-3.5)": ("gpt-3.5-turbo", "ChatgptAi"),
    "FreeGpt (GPT-3.5)": ("gpt-3.5-turbo", "FreeGpt"),
    "GptGo (GPT-3.5)": ("gpt-3.5-turbo", "GptGo"),
    "You (GPT-3.5)": ("gpt-3.5-turbo", "You"),
    "Llama (Llama 2 7B)": ("meta/llama-2-7b-chat", "Llama2"),
    "Llama (Llama 2 13B)": ("meta/llama-2-13b-chat", "Llama2"),
    "Llama (Llama 2 70B)": ("meta/llama-2-70b-chat", "Llama2"),
}


async def get_chat_response(
    messages: list[dict[str, str]],
    model: Model,
    provider: BaseProvider | None,
    timeout: int = gpt_settings.timeout,
    proxy: str | None = None,
) -> str | None:
    for attempt in range(gpt_settings.retries):
        response = await g4f.ChatCompletion.create_async(
            model=model, messages=messages, provider=provider, timeout=timeout, proxy=proxy
        )
        if response:
            return str(response)
        else:
            logger.warning(
                f"An empty response received from the {provider if provider else 'Default Provider'} "
                f"({model.name}). Retrying ({attempt+1}/{gpt_settings.retries})..."
            )
    return None


def retrieve_available_providers() -> list[str]:
    return list(MODELS_AND_PROVIDERS.keys())

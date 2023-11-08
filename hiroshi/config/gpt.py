from functools import lru_cache
from typing import Any

from pydantic import BaseSettings, Field

from hiroshi.config.telegram import telegram_settings


class GPTSettings(BaseSettings):
    assistant_prompt: str = Field(
        env="ASSISTANT_PROMPT",
        default=f"You're helpful and friendly assistant. Your name is {telegram_settings.bot_name}",
    )
    max_conversation_age_minutes: int = Field(env="MAX_CONVERSATION_AGE_MINUTES", default=60)
    max_history_tokens: int = Field(env="MAX_HISTORY_TOKENS", default=1800)
    proxy: str | None = Field(env="PROXY", default=None)
    timeout: int = Field(env="TIMEOUT", default=60)
    retries: int = Field(env="RETRIES", default=2)

    class Config:
        env_file = ".env"

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name == "gpt4_whitelist":
                return [str(username).strip().strip("@") for username in raw_val.split(",")]
            return cls.json_loads(raw_val)  # type: ignore

    @property
    def messages_ttl(self) -> int:
        return self.max_conversation_age_minutes * 60


@lru_cache()
def _get_gpt_settings() -> GPTSettings:
    return GPTSettings()


gpt_settings = _get_gpt_settings()

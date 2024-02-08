import time

from g4f.base_provider import BaseProvider
from g4f.models import Model, ModelUtils
from g4f.models import default as default_model
from g4f.Provider import ProviderUtils, RetryProvider
from loguru import logger
from pydantic import BaseModel, Field


class Message(BaseModel):
    id: int = Field(default_factory=time.time_ns)
    role: str
    content: str
    expire_at: float | None = None


class User(BaseModel):
    id: int
    provider_name: str | None = None
    model_name: str = "gpt_35_long"
    messages: list[Message] = Field(default_factory=list)

    @property
    def provider(self) -> BaseProvider | RetryProvider:
        if not self.provider_name:
            return default_model.best_provider
        if active_provider := ProviderUtils.convert.get(self.provider_name):
            return active_provider
        logger.error(f"Unsupported provider selected: {self.provider_name}. Replacing it with the default one.")
        return default_model.best_provider

    @property
    def model(self) -> Model:
        if active_model := ModelUtils.convert.get(self.model_name):
            return active_model
        return default_model

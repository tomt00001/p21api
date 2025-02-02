from typing import Tuple, Type

from p21api.config import Config
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource


class ConfigTest(Config):
    base_url: str = "http://example.com"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        # So dotenv file is not used in tests
        return (init_settings,)

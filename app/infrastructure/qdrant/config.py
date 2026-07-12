from abc import ABC, abstractmethod

from pydantic_settings import BaseSettings, SettingsConfigDict


class QdrantSettings(BaseSettings, ABC):
    vectors_size: int = 1024
    vectors_name: str = "dense"

    # 這個 Settings 類別的所有欄位，都從 QDRANT_ 開頭的環境變數讀
    model_config = SettingsConfigDict(env_prefix='QDRANT_')

    @property
    @abstractmethod
    def collection_name(self) -> str:
        ...


class RecipeQdrantSetting(QdrantSettings):
    @property
    def collection_name(self) -> str:
        return "recipes"


class YtQdrantSetting(QdrantSettings):
    @property
    def collection_name(self) -> str:
        return "yt_interview"
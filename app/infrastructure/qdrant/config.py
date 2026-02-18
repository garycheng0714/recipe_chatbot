from pydantic_settings import BaseSettings, SettingsConfigDict


class QdrantSettings(BaseSettings):
    recipe_collection_name: str = "recipes"
    intent_collection_name: str = "user_question_intent"
    vectors_size: int = 1024
    vectors_name: str = "dense"


    # 這個 Settings 類別的所有欄位，都從 QDRANT_ 開頭的環境變數讀
    model_config = SettingsConfigDict(env_prefix='QDRANT_')

qdrant_settings = QdrantSettings()
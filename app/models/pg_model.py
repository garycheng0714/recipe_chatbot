from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.database import Base

# 4. 定義資料模型 (對應資料表)
class PgRecipeModel(Base):
    __tablename__ = 'recipes'

    # --- 第一階段就能確定的欄位 (Non-nullable) ---
    id = Column(String(100), primary_key=True)
    source_url = Column(Text, unique=True, index=True)

    # 狀態管理: pending (待爬取), processing, completed, failed (永久失敗)
    status = Column(String(50), default='pending', index=True)

    # --- 第二階段才會補齊的欄位 (Nullable) ---
    name = Column(String(100), nullable=True)
    quantity = Column(String(50), nullable=True)
    ingredients = Column(JSONB, nullable=True)
    seasoning = Column(JSONB, nullable=True)
    category = Column(Text, nullable=True)
    tags = Column(ARRAY(String), nullable=True)

    # 時間戳 (這對 Backfill 非常有用)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # 重試與錯誤記錄
    retry_count = Column(Integer, default=0, nullable=True)
    last_error = Column(Text, nullable=True)  # 存儲最後一次的錯誤訊息或 Traceback

    chunks = relationship("PgRecipeChunkModel", back_populates="recipe", cascade="all, delete-orphan")


class PgRecipeChunkModel(Base):
    __tablename__ = 'recipe_chunks'

    id = Column(String(100), primary_key=True)
    parent_id = Column(String(100), ForeignKey('recipes.id', ondelete="CASCADE"), nullable=False)
    chunk_type = Column(String(30))
    content = Column(Text)

    recipe = relationship("PgRecipeModel", back_populates="chunks")
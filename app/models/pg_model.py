from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
import datetime
from app.database import Base

# 4. 定義資料模型 (對應資料表)
class PgRecipeModel(Base):
    __tablename__ = 'recipes'

    id = Column(String(100), primary_key=True)
    name = Column(String(100), nullable=False)
    source_url = Column(Text, unique=True, index=True)

    # 狀態管理: pending (待爬取), processing, completed, failed (永久失敗)
    status = Column(String(50), default='pending', index=True)

    # 重試與錯誤記錄
    retry_count = Column(Integer, default=0)
    last_error = Column(Text)  # 存儲最後一次的錯誤訊息或 Traceback

    quantity = Column(String(50))
    ingredients = Column(JSONB)
    seasoning = Column(JSONB, nullable=True)
    category = Column(Text)
    tags = Column(ARRAY(String))

    # 時間戳 (這對 Backfill 非常有用)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, onupdate=func.now())

    chunks = relationship("PgRecipeChunkModel", back_populates="recipe", cascade="all, delete-orphan")


class PgRecipeChunkModel(Base):
    __tablename__ = 'recipe_chunks'

    id = Column(String(100), primary_key=True)
    parent_id = Column(String(100), ForeignKey('recipes.id', ondelete="CASCADE"), nullable=False)
    chunk_type = Column(String(30))
    content = Column(Text)

    recipe = relationship("PgRecipeModel", back_populates="chunks")
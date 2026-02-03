from typing import Any

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship, selectinload, joinedload
import datetime
from client import Base

# 4. 定義資料模型 (對應資料表)
class RecipeModel(Base):
    __tablename__ = 'recipes'

    id = Column(String(100), primary_key=True)
    name = Column(String(100), nullable=False)
    quantity = Column(String(50))
    ingredients = Column(ARRAY(String))
    category = Column(Text)
    tags = Column(ARRAY(String))
    created_at = Column(DateTime, default=datetime.datetime.now)

    chunks = relationship("RecipeChunkModel", back_populates="recipe", cascade="all, delete-orphan")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "quantity": self.quantity,
            "ingredients": self.ingredients,
            "category": self.category,
            "tags": self.tags,
        }

class RecipeChunkModel(Base):
    __tablename__ = 'recipe_chunks'

    id = Column(String(100), primary_key=True)
    parent_id = Column(String(100), ForeignKey('recipes.id', ondelete="CASCADE"), nullable=False)
    chunk_type = Column(String(30))
    content = Column(Text)

    recipe = relationship("RecipeModel", back_populates="chunks")
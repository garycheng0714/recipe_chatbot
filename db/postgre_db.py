from typing import Any

from dotenv import load_dotenv

from recipe_entity import RecipeDocument

load_dotenv()

import os

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy import select
import datetime


# 1. 設定連線字串 (格式: postgresql://使用者:密碼@主機:埠號/資料庫名)
DB_URL = f"postgresql://postgres:{os.getenv("OPENAI_API_KEY")}@localhost:5432/recipe_orm_db"

# 2. 如果資料庫不存在，就建立它
# if not database_exists(DB_URL):
#     create_database(DB_URL)
#     print("資料庫 recipe_orm_db 建立成功！")

# # 3. 初始化 Engine 與 Base
# engine = create_engine(DB_URL)
Base = declarative_base()


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

class PostgreDB:
    def __init__(self):
        self.session = sessionmaker(bind=create_engine(DB_URL))()
        self.stmt = select(RecipeModel)

    def add_recipe(self, recipe: RecipeModel):
        self.session.add(recipe)

    def add_chunk(self, chunk: RecipeChunkModel):
        self.session.add(chunk)

    def commit(self):
        self.session.commit()

    def close(self):
        self.session.close()

    def select_all(self):
        return self.session.execute(self.stmt).scalars(select(RecipeChunkModel)).all()

# 5. 建立資料表 (將定義好的 Model 映射到資料庫)
# Base.metadata.create_all(engine)
# print("資料表已同步完成！")

if __name__ == "__main__":
    try:
        db = PostgreDB()
        result = db.select_all()
        for r in result:
            print(r.to_dict())
    finally:
        db.close()
from typing import Literal

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import select
from models import RecipeChunkModel, RecipeModel
import models, database

# 自動建立資料表 (如果不存在的話)
models.Base.metadata.create_all(bind=database.engine)

# 1. 建立一個 FastAPI 實例
app = FastAPI()

# 取得資料庫連線的工具函數
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 2. 定義一個路徑操作 (Path Operation)
@app.get("/")
def read_root():
    return {"Hello": "World"}

def convert_recipe_to_dict(model: Literal["RecipeModel", "RecipeChunkModel"]):
    if isinstance(model, RecipeChunkModel):
        recipe = model.recipe
    else:
        recipe = model

    recipe_dict = recipe.to_dict()

    for chunk in recipe.chunks:
        recipe_dict[chunk.chunk_type] = chunk.content

    return recipe_dict

# 3. 定義一個帶有參數的路徑
@app.get("/recipe/{recipe_id}")
def read_item(recipe_id: str, db: Session = Depends(get_db)):
    if any(word in recipe_id for word in ["overview", "instruction"]):
        stmt = (
            select(RecipeChunkModel)
            .where(RecipeChunkModel.id == recipe_id)
            .options(
                joinedload(RecipeChunkModel.recipe)
                .selectinload(RecipeModel.chunks)
            )
        )
    else:
        stmt = (
            select(RecipeModel)
            .options(selectinload(RecipeModel.chunks))
            .where(RecipeModel.id == recipe_id)
        )

    result_model = db.execute(stmt).scalar_one_or_none()

    return convert_recipe_to_dict(result_model)
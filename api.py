from contextlib import asynccontextmanager
from typing import Union, Any

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import select
from models import RecipeChunkModel, RecipeModel
from schemas import RecipeRead, RecipeReadFlatten
from client import get_db
import models, client

# 自動建立資料表 (如果不存在的話)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: 建立 DB schema
    async with client.engine.begin() as conn:
        await conn.run_sync(client.Base.metadata.create_all)
    yield
    # Shutdown: 可以在這裡釋放資源、關閉連線池
    await client.engine.dispose()

# 1. 建立一個 FastAPI 實例
app = FastAPI(lifespan=lifespan)


# 2. 定義一個路徑操作 (Path Operation)
@app.get("/")
def read_root():
    return {"Hello": "World"}


# 3. 定義一個帶有參數的路徑
@app.get("/recipe/{recipe_id}", response_model=RecipeRead)
async def read_item(recipe_id: str, db: Session = Depends(get_db)):
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

    result = await db.execute(stmt)
    obj = result.scalar_one_or_none()

    # 安全檢查：找不到就報 404，不要讓後續程式碼崩潰
    if obj is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # 如果查詢結果是 Chunk，則取其 recipe 父物件
    target_obj = obj.recipe if isinstance(obj, models.RecipeChunkModel) else obj

    # 使用 RecipeRead 進行轉換與攤平
    return RecipeReadFlatten.model_validate(target_obj).model_dump()
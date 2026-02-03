from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from schemas import RecipeRead, RecipeReadFlatten
from app.client import get_db, get_es
from app.models import (
    RecipeChunkModel,
    EsPointsModel
)
from app.repositories import (
    PgRepository,
    ElasticSearchRepository
)
import app.database as database


# 自動建立資料表 (如果不存在的話)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: 建立 DB schema
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)
    yield
    # Shutdown: 可以在這裡釋放資源、關閉連線池
    await database.engine.dispose()

# 1. 建立一個 FastAPI 實例
app = FastAPI(lifespan=lifespan)


# 2. 定義一個路徑操作 (Path Operation)
@app.get("/")
def read_root():
    return {"Hello": "World"}


# 3. 定義一個帶有參數的路徑
@app.get("/recipe/{recipe_id}", response_model=RecipeRead)
async def read_item(recipe_id: str, pg_service: PgRepository = Depends(get_db)):
    obj = await pg_service.fetch_recipe(recipe_id)

    # 安全檢查：找不到就報 404，不要讓後續程式碼崩潰
    if obj is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # 如果查詢結果是 Chunk，則取其 recipe 父物件
    target_obj = obj.recipe if isinstance(obj, RecipeChunkModel) else obj

    # 使用 RecipeRead 進行轉換與攤平
    return RecipeReadFlatten.model_validate(target_obj).model_dump()

@app.get("/es/{query}")
async def es_search(query: str, es: ElasticSearchRepository = Depends(get_es)):
    result = await es.search(query)
    points = EsPointsModel(**result)
    return points
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException

from app.services.retriever import Retriever
from app.schema.api_schemas import RecipeRead, RecipeReadFlatten

from qdrant_client.models import (
    VectorParams,
    Distance
)

from app.client import (
    get_db,
    get_es,
    get_qdrant,
    es_client,
    qdr_client,
    model
)

from app.models import (
    PgRecipeChunkModel,
    EsPointsModel
)

from app.repositories import (
    ElasticSearchRepository,
    QdrantRepository
)

import app.database as database


# 自動建立資料表 (如果不存在的話)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup: 建立 PG schema ---
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)

    # warm-up to avoid slow response at first time encode
    model.encode(["startup warm-up"])

    # --- Startup: 建立 Qdrant collection ---
    # if not await qdr_client.collection_exists(qdr_collection_name):
    #     await qdr_client.create_collection(
    #         collection_name=qdr_collection_name,
    #         vectors_config={
    #             "dense": VectorParams(
    #                 size=1024,  # BGE-M3 的維度
    #                 distance=Distance.COSINE
    #             )
    #         }
    #     )

    yield
    # Shutdown: 可以在這裡釋放資源、關閉連線池
    await database.engine.dispose()
    # await qdr_client.close()  Qdrant client 不需要手動 shutdown，因為它的 async request 是輕量且短暫的。
    await es_client.close()     #Elasticsearch async client 因為長期維持連線池，所以必須在 lifespan shutdown 時關閉

# uvicorn app.main:app
# 1. 建立一個 FastAPI 實例
app = FastAPI(lifespan=lifespan)


# 2. 定義一個路徑操作 (Path Operation)
@app.get("/")
def read_root():
    return {"Hello": "World"}

# 輔助函式：建立 Service
async def get_search_service(
    es=Depends(get_es),
    qdr=Depends(get_qdrant),
    db=Depends(get_db)
):
    return Retriever(es, qdr, db)

# 3. 定義一個帶有參數的路徑
@app.get("/recipe/{query_text}")
async def search_recipe(
        query_text: str,
        retriever: Retriever = Depends(get_search_service)
):
    intent_point = await retriever.search_intent(query_text)

    if intent_point.score < 0.6:
        raise HTTPException(status_code=404, detail="Recipe not found")

    intent = intent_point.payload["intent"]

    obj_list, score_list = await retriever.search_recipe(query_text, intent)

    # 安全檢查：找不到就報 404，不要讓後續程式碼崩潰
    if obj_list is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    result = []

    for idx, obj in enumerate(obj_list):
        # 如果查詢結果是 Chunk，則取其 recipe 父物件
        target_obj = obj.recipe if isinstance(obj, PgRecipeChunkModel) else obj

        # 使用 RecipeRead 進行轉換與攤平
        recipe_read = RecipeReadFlatten.model_validate(target_obj)
        recipe_read.set_score(score_list[idx])
        result.append(recipe_read.model_dump())

    return result

@app.get("/es/{query}")
async def es_search(query: str, es: ElasticSearchRepository = Depends(get_es)):
    result = await es.search(query)
    points = EsPointsModel(**result)
    return points

@app.get("/semantic/{query}")
async def semantic_search(query: str, qdr: QdrantRepository = Depends(get_qdrant)):
    qdr_res = await qdr.search_intent(query)
    # return [str(point.payload["id"]) for point in qdr_res.points]
    return qdr_res.points[0]

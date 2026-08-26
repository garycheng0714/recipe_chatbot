from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

from app.hydrator.recipe.recipe_hydrator import RecipeHydrator
from app.hydrator.yt.yt_hydrator import YtHydrator
from app.retriever.hybrid_retriever import HybridRetriever
from app.retriever.retriever_protocol import RetrieverBase

from app.client import (
    get_db,
    get_es_retriever,
    get_qdr_retriever,
    get_hybrid_retriever,
    es_client,
    get_yt_hybrid_retriever,
    get_yt_db, get_yt_es_retriever, get_yt_qdr_retriever, get_translate_agent, get_generation_agent, get_translator
)

import app.database as database
from app.services.rag_service import RagService
from app.services.retriever_service import RetrievalService


# 自動建立資料表 (如果不存在的話)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup: 建立 PG schema ---
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)

    yield
    # Shutdown: 可以在這裡釋放資源、關閉連線池
    await database.engine.dispose()
    await es_client.close()     #Elasticsearch async client 因為長期維持連線池，所以必須在 lifespan shutdown 時關閉

# uvicorn app.main:app
# 1. 建立一個 FastAPI 實例
app = FastAPI(lifespan=lifespan)


# 2. 定義一個路徑操作 (Path Operation)
@app.get("/")
def read_root():
    return {"Hello": "World"}

# 輔助函式：建立 Service
async def get_recipe_retrieval_service(
    hybrid_retriever=Depends(get_hybrid_retriever),
    db=Depends(get_db)
):
    hydrator = RecipeHydrator(db)
    return RetrievalService(hybrid_retriever, hydrator)

async def get_yt_retrieval_service(
    hybrid_retriever=Depends(get_yt_hybrid_retriever),
    db=Depends(get_yt_db)
):
    hydrator = YtHydrator(db)
    return RetrievalService(hybrid_retriever, hydrator)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 3. 定義一個帶有參數的路徑
@app.get("/recipe/{query_text}")
async def search_recipe(
    query_text: str,
    service: RetrievalService = Depends(get_recipe_retrieval_service)
):
    obj_list = await service.retrieve(query_text, 5)

    # 安全檢查：找不到就報 404，不要讓後續程式碼崩潰
    if obj_list is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return obj_list


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    translate_agent=Depends(get_translate_agent),
    generation_agent=Depends(get_generation_agent),
    translator=Depends(get_translator),
    retrieval_service: RetrievalService = Depends(get_yt_retrieval_service)
):
    rag_service = RagService(translate_agent, generation_agent, retrieval_service, translator)

    result = await rag_service.execute(request.message)

    return ChatResponse(answer=result)


@app.get("/yt/es/{query}")
async def es_search(query: str, retriever: RetrieverBase = Depends(get_yt_es_retriever)):
    return await retriever.retrieve(query, 5)

@app.get("/yt/qdr/{query}")
async def qdr_search(query: str, retriever: RetrieverBase = Depends(get_yt_qdr_retriever)):
    return await retriever.retrieve(query, 5)

@app.get("/es/{query}")
async def es_search(query: str, retriever: RetrieverBase = Depends(get_es_retriever)):
    return await retriever.retrieve(query, 10)

@app.get("/qdr/{query}")
async def qdr_search(query: str, retriever: RetrieverBase = Depends(get_qdr_retriever)):
    return await retriever.retrieve(query, 3)

@app.get("/yt/hybrid/{query}")
async def qdr_search(query: str, retriever: HybridRetriever = Depends(get_yt_hybrid_retriever)):
    return await retriever.retrieve(query, 5)

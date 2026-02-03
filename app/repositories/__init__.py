from .pg_repository import PgRepository
from .es_repository import ElasticSearchRepository
from .qdr_repository import QdrantRepository

"""
Repository
功能：直接跟資料來源打交道，負責 CRUD、查詢、或原始向量檢索
資料來源範例：

資料來源	                   Repository 例子
PgRepository	           PgRepository（操作 SQLAlchemy ORM）
ElasticSearchRepository	   ESRepository（操作 ES query DSL）
Qdrant	QdrRepository（操作向量搜尋）

特點：
只做資料層邏輯，不處理商業規則
回傳原始物件（可以是 ORM object、Pydantic model、向量結果 dict）
"""
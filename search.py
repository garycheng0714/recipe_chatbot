from db_utils import ElasticSearchHelper
from db_utils import QdrantVectorStore
from entity import EsPointsModel
import asyncio


def reciprocal_rank_fusion(search_results_list, k=60):
    """
    search_results_list: 一個列表的列表，例如 [[doc_id1, doc_id2], [doc_id2, doc_id3]]
    k: 平滑常數，預設 60
    """
    fused_scores = {}

    for rank_list in search_results_list:
        for rank, doc_id in enumerate(rank_list):
            # rank 從 0 開始，所以公式中要 +1
            # 如果找不到 doc_id，就回傳 0，然後再加分數
            fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1 / (k + (rank + 1))

    # 按分數從高到低排序
    """
    fused_scores 是一個字典（Dictionary），長得像這樣： {"doc_A": 0.032, "doc_B": 0.015, "doc_C": 0.045}
    當你執行 .items() 時，它會變成一個列表包著元組（list of tuples）： [("doc_A", 0.032), ("doc_B", 0.015), ("doc_C", 0.045)]
    用分數做排序，分數愈高越前面
    """
    sorted_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results


async def hybrid_search(query_text, top_n=10):
    es = ElasticSearchHelper()
    qdrant = QdrantVectorStore()

    # --- Step 1 & 2: 同時發送請求 (Parallel Execution) ---
    # 使用 asyncio.gather 同時啟動 ES 和 Qdrant 的搜尋
    # 這裡建議把檢索數量 (k) 放大一點，例如 top_n * 2，RRF 的效果會更好
    search_k = top_n * 2

    # 同時執行兩個 task
    es_res = es.search(query_text=query_text, size=search_k)
    qd_res = qdrant.search(query_text=query_text, k=search_k)

    # 等待兩者完成
    es_res, qd_res = await asyncio.gather(es_res, qd_res)

    # --- Step 3: 解析結果 ---
    # 處理 Elasticsearch 結果
    es_points = EsPointsModel(**es_res)
    es_ids = [hit.field_source.id for hit in es_points.hits.hits]
    print(f"BM25: {es_ids}\n")

    # 處理 Qdrant 結果
    qd_ids = [str(point.payload["id"]) for point in qd_res.points]
    print(f"Vector: {qd_ids}\n")

    # --- Step 4: 套用 RRF ---
    fused_results = reciprocal_rank_fusion([es_ids, qd_ids], k=60)

    # 取出前 N 名的 ID
    final_top_ids = [doc_id for doc_id, score in fused_results[:top_n]]

    return final_top_ids

if __name__ == '__main__':
    from db_utils import PostgreDB
    db = PostgreDB()

    result = asyncio.run(
        hybrid_search(query_text="鹽昆布奶油烤飯糰", top_n=5)
    )

    print(result)


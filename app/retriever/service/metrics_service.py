import asyncio
from enum import StrEnum

import pandas as pd

from app.retriever.enums import Retriever
from app.retriever.model import TestSet
from app.retriever.service.calculate_service import CalculateService

class Columns(StrEnum):
    METHOD = "Method"
    QUERY = "Query"
    RECALL_5 = "Recall@5 (Average)"
    MRR_5 = "MRR@5 (Average)"


class MetricsService:

    retrievers = [
        Retriever.BM25,
        Retriever.VECTORS,
        Retriever.HYBRID
    ]

    @classmethod
    async def create_metrics(
        cls,
        calculate_service: CalculateService,
        test_sets: list[TestSet],
    ):
        if not calculate_service.calculator.allow_empty_relevant_ids:
            test_sets = [t for t in test_sets if t.relevant_ids]

        tasks = [
            calculate_service.calculate(retriever.get_retriever(), test_sets)
            for retriever in cls.retrievers
        ]

        retriever_results = await asyncio.gather(*tasks)

        queries = [test.question for test in test_sets]

        # 直接構建矩陣字典: { Method_Name: [score_1, score_2, ...] }
        data = {
            retriever: [float(r) for r in score_list]
            for retriever, score_list in zip(cls.retrievers, retriever_results)
        }

        # Data shape: 列為 Query, 欄為 Method，轉置後轉回想要的 shape
        df = pd.DataFrame(data, index=queries).T
        df.index.name = Columns.METHOD

        metrics_name = calculate_service.calculator.metrics_name

        df[f"{metrics_name}@5 (Average)"] = df.mean(axis=1)

        return df


    @classmethod
    def merge(cls, df_recall: pd.DataFrame, df_mrr: pd.DataFrame):

        columns = [col for col in df_recall.columns if 'Average' not in col] + ['Recall@5 (Average)', 'MRR@5 (Average)']

        # 1. 幫 df_mrr 加標籤：一般欄位叫 'MRR'，平均欄位第二層留空 ''
        df_mrr.columns = pd.MultiIndex.from_tuples(
            [(col, '') if 'Average' in col else (col, 'MRR') for col in df_mrr.columns]
        )

        # 2. 幫 df_recall 加標籤：一般欄位叫 'Recall'，平均欄位第二層留空 ''
        df_recall.columns = pd.MultiIndex.from_tuples(
            [(col, '') if 'Average' in col else (col, 'Recall') for col in df_recall.columns]
        )

        # 3. 左右直接拼起來 (axis=1)
        df_final = pd.concat([df_mrr, df_recall], axis=1)

        # 4. 排序欄位 (讓 MRR 和 Recall 交錯放在一起，並且把 Average 移到最後)
        df_final = df_final.sort_index(axis=1, level=0).reindex(columns=columns, level=0)

        # 解除欄位數限制（顯示所有欄位）
        pd.set_option('display.max_columns', None)

        # 解除單行寬度限制（防止自動換行折疊）
        pd.set_option('display.width', 1000)

        return df_final

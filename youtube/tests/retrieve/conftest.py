import json
from typing import List

import pandas as pd
import pytest
from pydantic import TypeAdapter

from app.retriever.metrics.mrr import MRR
from app.retriever.metrics.recall_metrics import RecallMetrics
from app.retriever.retriever_protocol import RetrieverBase
from app.retriever.model import TestSet
from app.retriever.service.calculate_service import CalculateService
from app.retriever.service.metrics_service import MetricsService


@pytest.fixture(scope="class")
def data_test_set_reader():

    def _reader(file_path: str) -> list[TestSet]:
        with open(file_path, 'r') as f:
            pairs = json.load(f)
        return TypeAdapter(List[TestSet]).validate_python(pairs)

    return _reader


@pytest.fixture
def calculate_recall():
    async def _calculate_recall(retriever: RetrieverBase, test_sets: list[TestSet]) -> list[float]:
        recall_service = CalculateService()
        return await recall_service.calculate(retriever, test_sets)
    return _calculate_recall


@pytest.fixture
def create_recall_5_metrics():
    async def _create_metrics(test_sets: list[TestSet]) -> pd.DataFrame:

        calculate_service = CalculateService(calculator=RecallMetrics())

        df = await MetricsService.create_metrics(calculate_service, test_sets)

        return df

    return _create_metrics


@pytest.fixture
def create_mrr_5_metrics():
    async def _create_mrr_metrics(test_sets: list[TestSet]) -> pd.DataFrame:

        calculate_service = CalculateService(calculator=MRR())

        df = await MetricsService.create_metrics(calculate_service, test_sets)

        return df

    return _create_mrr_metrics

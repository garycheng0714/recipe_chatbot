import json
from enum import StrEnum
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
from app.retriever.service.report.report_generator import generate_benchmark_html


@pytest.fixture(scope="class")
def data_test_set_reader():

    def _reader(file_path: str) -> list[TestSet]:
        with open(file_path, 'r') as f:
            pairs = json.load(f)
        return TypeAdapter(List[TestSet]).validate_python(pairs)

    return _reader

class FileType(StrEnum):
    BASE = "base"
    CURRENT = "curr"


@pytest.fixture
def create_metrics_json_data(request):
    def _export_json(df: pd.DataFrame, file_type: FileType = FileType.CURRENT):
        report_dir = request.path.parent / "report"
        prefix_name = request.path.stem.removeprefix('test_')

        file = report_dir / f"{prefix_name}_{file_type}.json"

        if file_type == FileType.BASE:
            for t in [FileType.BASE, FileType.CURRENT]:
                (report_dir / f"{prefix_name}_{t}.json").unlink(missing_ok=True)

        df.to_json(path_or_buf=file, indent=2, force_ascii=False)
    return _export_json


@pytest.fixture
def check_metrics_diff(request):
    def _check_metrics_diff():
        report_dir = request.path.parent / "report"
        prefix_name = request.path.stem.removeprefix('test_')

        base_file   = report_dir / f"{prefix_name}_base.json"
        curr_file   = report_dir / f"{prefix_name}_curr.json"
        output_file = report_dir / f"{prefix_name}_diff.html"

        if base_file.exists() and curr_file.exists():
            with open(base_file, 'r') as f:
                base_data = json.load(f)

            with open(curr_file, 'r') as f:
                curr_data = json.load(f)

            result = generate_benchmark_html(base_data, curr_data, output_filename=output_file)
        else:
            print("No file to check diff")
            result = True

        return result

    return _check_metrics_diff


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


@pytest.fixture
def create_recall_mrr_metrics():
    async def _create_metrics(test_sets: list[TestSet]) -> pd.DataFrame:
        calculate_service = CalculateService(calculator=MRR())
        df_mrr = await MetricsService.create_metrics(calculate_service, test_sets)

        calculate_service = CalculateService(calculator=RecallMetrics())
        df_recall = await MetricsService.create_metrics(calculate_service, test_sets)

        df = MetricsService.merge(df_recall, df_mrr)

        return df
    return _create_metrics

import asyncio
import json
from typing import List

import pytest
from deepeval.evaluate import evaluate
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
from deepeval.models import OllamaModel
from deepeval.test_case import LLMTestCase
from pydantic import TypeAdapter

from app.agent.generation import GenerationAgent
from app.client import get_yt_rerank_retriever
from app.retriever.model import TestSet


@pytest.fixture
def agent():
    return GenerationAgent()

@pytest.fixture
def retriever():
    return get_yt_rerank_retriever()

@pytest.fixture
def judge_model():
    return OllamaModel(
        model='llama3:8b',
        base_url='http://localhost:11434'
    )

@pytest.fixture(scope="class")
def data_test_set_reader():

    def _reader(file_path: str) -> list[TestSet]:
        with open(file_path, 'r') as f:
            pairs = json.load(f)
        return TypeAdapter(List[TestSet]).validate_python(pairs)

    return _reader


@pytest.mark.asyncio
async def test_answer_question(agent, retriever, judge_model, data_test_set_reader):

    question = "What was the difference between his failed first attempt at Monza and his successful attempt in Vienna?"

    result = await retriever.retrieve(question, 5)

    chunks = [r.answer for r in result]

    answer = await agent.run(chunks, question)

    test_cases = [
        LLMTestCase(
            input=question,
            actual_output=answer,
            retrieval_context=chunks
        )
    ]

    # 手動印出 LLM 實際回答
    print("\n" + "=" * 20 + " [LLM Actual Output] " + "=" * 20)
    print(answer)
    print("=" * 61 + "\n")

    faithfulness = FaithfulnessMetric(threshold=0.7, model=judge_model, verbose_mode=True)
    relevancy = AnswerRelevancyMetric(threshold=0.7, model=judge_model, verbose_mode=True)

    evaluate(test_cases, [faithfulness, relevancy])

    # 或事後看
    print(faithfulness.reason)
    print(faithfulness.score_breakdown)  # 如果有提供 claim-level 細節
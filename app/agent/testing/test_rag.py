import asyncio
import json
import os
from typing import List

import pytest
from deepeval.evaluate import evaluate
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
from deepeval.models import GeminiModel
from deepeval.test_case import LLMTestCase
from pydantic import TypeAdapter
from pydantic_ai import capture_run_messages

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
    return GeminiModel(
        model='gemini-2.5-flash-lite',
        api_key=os.environ.get("GOOGLE_API_KEY"),
        temperature=0.0
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
    test_sets = data_test_set_reader("youtube/tests/retrieve/assets/golden_set.json")

    questions = [t.question for t in test_sets]

    retriever_tasks = [
        retriever.retrieve(q, 5)
        for q in questions
    ]

    retriever_results = await asyncio.gather(*retriever_tasks)

    chunks = []

    for result in retriever_results:
        chunks.append(
            [
                r.answer for r in result
            ]
        )

    agent_task = [
        agent.run(chunk, q)
        for chunk, q in zip(chunks, questions)
    ]

    capture_run_messages()

    agent_results = await asyncio.gather(*agent_task)

    test_cases = [
        LLMTestCase(
            input=question,
            actual_output=answer,
            retrieval_context=chunk
        )
        for question, answer, chunk in zip(questions, agent_results, chunks)
    ]

    # 手動印出 LLM 實際回答
    # print("\n" + "=" * 20 + " [LLM Actual Output] " + "=" * 20)
    # print(answer)
    # print("=" * 61 + "\n")

    faithfulness = FaithfulnessMetric(threshold=0.7, model=judge_model, verbose_mode=True)
    relevancy = AnswerRelevancyMetric(threshold=0.7, model=judge_model, verbose_mode=True)

    evaluate(test_cases, [faithfulness, relevancy])

    # 或事後看
    print(faithfulness.reason)
    print(faithfulness.score_breakdown)  # 如果有提供 claim-level 細節
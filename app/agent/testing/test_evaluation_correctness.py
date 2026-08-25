import asyncio
import json
from typing import List

import pytest
from deepeval.evaluate import evaluate
from deepeval.metrics import GEval
from deepeval.test_case import SingleTurnParams, LLMTestCase
from pydantic import TypeAdapter

from app.agent.generation import GenerationAgent
from deepeval.models import OllamaModel

from app.client import get_yt_retrieval_service
from app.retriever.model import TestSet


@pytest.fixture
def agent():
    return GenerationAgent()


@pytest.fixture
def judge_model():
    return OllamaModel(
        model='llama3:8b',
        temperature=0
    )


@pytest.fixture
def retrieval_service():
    return get_yt_retrieval_service()


@pytest.fixture(scope="class")
def data_test_set_reader():

    def _reader(file_path: str) -> list[TestSet]:
        with open(file_path, 'r') as f:
            pairs = json.load(f)
        return TypeAdapter(List[TestSet]).validate_python(pairs)

    return _reader


@pytest.mark.asyncio
async def test_evaluation_correctness(judge_model, data_test_set_reader, retrieval_service, agent):
    correctness = GEval(
        name="Correctness",
        evaluation_steps=[
            "Identify what information the question is asking for.",
            "Determine the key factual or semantic claim made by the actual answer.",
            "Compare the actual answer with the expected answer based on semantic meaning, not exact wording.",
            "Determine whether the actual answer directly answers the question.",
            "Accept concise answers when they correctly capture the key information requested by the question.",
            "Penalize answers only when they are factually incorrect, incomplete in a way that changes the meaning, contradictory, or fail to answer the question."
        ],
        criteria=(
            """
            Evaluate whether the actual answer correctly answers the question
            and is semantically consistent with the expected answer.
            
            The actual answer does not need to use the same wording as the expected answer.
            Concise answers should receive a high score when they correctly capture
            the key information requested by the question.
            
            Do not penalize an answer merely because it provides less detail than
            the expected answer, unless the missing information is necessary to
            answer the question correctly.
            """
        ),
        evaluation_params=[
            SingleTurnParams.INPUT,
            SingleTurnParams.ACTUAL_OUTPUT,
            SingleTurnParams.EXPECTED_OUTPUT
        ],
        threshold=0.7,
        model=judge_model
    )

    test_sets = data_test_set_reader("youtube/tests/retrieve/assets/golden_set.json")

    questions = [t.question for t in test_sets]

    retriever_tasks = [
        retrieval_service.retrieve(q, 5)
        for q in questions
    ]

    retriever_results = await asyncio.gather(*retriever_tasks)

    expected_answers = [t.reference_answer for t in test_sets]

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

    agent_results = await asyncio.gather(*agent_task)


    test_cases = [
        LLMTestCase(
            input=question,
            actual_output=answer,
            expected_output=expected_answer
        )
        for question, answer, expected_answer in zip(questions, agent_results, expected_answers)
    ]


    evaluate(test_cases, [correctness])
import pytest
from deepeval.metrics import GEval
from deepeval.test_case import SingleTurnParams, LLMTestCase

from app.agent.generation import GenerationAgent
from deepeval.models import OllamaModel


@pytest.fixture
def agent():
    return GenerationAgent()


@pytest.fixture
def judge_model():
    return OllamaModel(
        model='llama3:8b',
        temperature=0
    )


@pytest.mark.asyncio
async def test_evaluation_correctness(judge_model):
    correctness = GEval(
        name="Correctness",
        evaluation_steps=[
            "Determine what information the question is asking for.",
            "Identify the factual claims in the answer.",
            "Verify each claim against the provided context.",
            "Check whether the answer directly addresses the question.",
            "Penalize factual errors, contradictions, or unsupported information.",
        ],
        criteria=(
            "Determine whether the actual output is factually correct according to the expected output."
        ),
        evaluation_params=[
            SingleTurnParams.INPUT,
            SingleTurnParams.ACTUAL_OUTPUT,
            SingleTurnParams.EXPECTED_OUTPUT
        ],
        threshold=0.7,
        model=judge_model
    )

    test_case = LLMTestCase(
        input="How much slower is his easy run pace compared to his marathon pace, which takes under two hours?",
        actual_output="According to the information provided, Eliud Kipchoge's easy run pace is about 5 minutes per kilometer, which is about 2 minutes and 10 seconds per kilometer slower than his 2-hour marathon pace.",
        expected_output="is about 2 minutes and 10 seconds per kilometer slower than a marathon pace.",
    )

    correctness.measure(test_case)

    print(correctness.score)
    print(correctness.reason)

    assert correctness.success
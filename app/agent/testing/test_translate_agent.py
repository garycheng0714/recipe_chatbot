import pytest

from app.agent.translate import TranslateAgent

ENGLISH_PASSTHROUGH_CASES = [
    "What was the difference between his failed first attempt at Monza and his successful attempt in Vienna?",
    "How does he view self-improvement and the learning process in running?",
    "What analogy did he use to describe his mindset during his first Breaking2 attempt?",
    "How much slower is his easy run pace compared to his sub-two-hour marathon pace?",
    "What technology does his team use to monitor his nutrition and blood glucose in real time?",
    "What key training allows its body to sustain high speed for a long time?",
    "At the Kaptagat training camp, how does his lifestyle and training differ from other athletes despite being a world record holder?",
    "What advice would he give recreational runners about planning their training?",
    "Even after a hard session, what state does he try to finish training in?",
    "According to the speaker, what is improvement closely linked with?",
    "What kind of program tracking does the speaker recommend for recreational runners to improve?",
    "How does the speaker suggest recreational runners can better understand their own bodies during training?",
    "What specific equipment does the speaker suggest runners get for training?",
    "What is one key psychological aspect the speaker emphasizes for runners to embrace during their runs?",
    "How quickly does the speaker suggest improvement will occur for runners who are dedicated to their training?",
]


@pytest.fixture
def agent():
    return TranslateAgent()

@pytest.mark.asyncio
@pytest.mark.parametrize("query", ENGLISH_PASSTHROUGH_CASES)
async def test_translate_agent(query, agent):
    output = await agent.run(query)

    assert query == output.translated_en


@pytest.mark.asyncio
@pytest.mark.parametrize("query, keyword", [
    ("他的 recovery 訓練是怎樣？", "recovery"),
    ("Kipchoge 的 marathon PB 是多少？", "marathon"),
    ("Long run 重要嗎？", "long run"),
])
async def test_translate_zh(agent, query, keyword):

    output = await agent.run(query)

    assert keyword in output.translated_en.lower()


@pytest.mark.asyncio
async def test_translate_empty(agent):
    output = await agent.run("")

    assert output == "請提供問題"


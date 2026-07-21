import asyncio
import json

from pydantic import BaseModel, Field, TypeAdapter
from pydantic_ai import Agent

from app.agent.task_processor import TaskProcessor
from web_crawler.requester import HttpxRequester

QUERIES = [
        {
            "query": "What was the difference between his failed first attempt at Monza and his successful attempt in Vienna?",
        },
        {
            "query": "How does he view self-improvement and the learning process in running?",
        },
        {
            "query": "What analogy did he use to describe his mindset during his first Breaking2 attempt?",
        },
        {
            "query": "How much slower is his easy run pace compared to his sub-two-hour marathon pace?",
        },
        {
            "query": "What technology does his team use to monitor his nutrition and blood glucose in real time?",
        },
        {
            "query": "What key training lets his body sustain high speed for a long time?"
        },
        {
            "query": "At the Kaptagat training camp, how does his lifestyle and training differ from other athletes despite being a world record holder?",
        },
        {
            "query": "What advice would he give recreational runners about planning their training?"
        },
        {
            "query": "Even after a hard session, what state does he try to finish training in?",
        },
    ]

VERIFY_PROMPT_TEMPLATE = """You are helping build a golden test set for evaluating a retrieval system.

    Query: "{query}"

    Below are the top-{top_k} search results returned for this query. Each is a QA pair
    extracted from an interview transcript.

    {candidates}

    For each candidate, judge whether it DIRECTLY and SUBSTANTIVELY answers the query.

    Classify each candidate id into exactly one of:
    - "must_have": the answer content directly and clearly answers the query
    - "nice_to_have": partially relevant, touches the topic but doesn't fully answer it
    - (omit entirely if irrelevant — don't list irrelevant ids anywhere)

    Be strict about "must_have" — only use it when the answer would genuinely satisfy
    someone asking this exact query. Don't force a match if nothing qualifies.
    """


class LabelResult(BaseModel):
    must_have: list[str] = Field(description="The id of the answer that directly and clearly answers the query")
    nice_to_have: list[str] = Field(description="The id of the answer that partially relevant, touches the topic but doesn't fully answer it")
    reasoning: dict[str, str] = Field(description="The reason why choose the answer")


def format_candidates(results: list) -> str:
    lines = []
    for r in results:
        lines.append(
            f"[id: {r.get('id')}]\n"
            f"answer: {r.get('answer')}\n"
        )
    return "\n".join(lines)

if __name__ == '__main__':
    SEARCH_API_BASE = "http://127.0.0.1:8000/yt/search"

    async def main():
        async with HttpxRequester() as requester:
            queries = [q.values() for q in QUERIES]

            tasks = [requester.request(url=f"{SEARCH_API_BASE}/{q}") for q in queries]

            resp = await asyncio.gather(*tasks)

            candidates = [format_candidates(json.loads(r)) for r in resp]

            prompts = [
                VERIFY_PROMPT_TEMPLATE.format(query=query, top_k=5, candidates=candidate)
                for query, candidate in zip(queries, candidates)
            ]

            # 1. 建立 Agent，直接指定 Gemini 模型的名稱
            agent = Agent(
                model='gemini-2.5-flash',
                output_type=LabelResult
            )

            processor = TaskProcessor(agent=agent)

            result = await processor.process_all(prompts)

            adapter = TypeAdapter(list[LabelResult])

            with open("result.json", "w", encoding="utf-8") as f:
                f.write(adapter.dump_json(result, indent=2).decode())


    asyncio.run(main())
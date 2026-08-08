import asyncio
import json

from pydantic import BaseModel, Field, TypeAdapter
from pydantic_ai import Agent

from app.agent.task_processor import TaskProcessor
from web_crawler.requester import HttpxRequester

QUERIES = [
        {
            "query": "How can recreational runners establish a structured weekly program and maintain a detailed running log to track their long-term progress?",
        },
        {
            "query": "How can runners develop better body awareness to distinguish between normal fatigue and injury risks during their training adaptation?",
        },
        {
            "query": "Beyond selecting appropriate running gear, how can athletes effectively utilize heart rate monitoring and physiological data to guide their training?",
        },
        {
            "query": "How can runners maintain a positive psychological mindset and ensure genuine enjoyment while staying committed to their training goals?",
        },
        {
            "query": "Since performance gains require continuous effort, how can recreational runners build long-term consistency and stay driven by dedication over weeks and months?",
        }
    ]

VERIFY_PROMPT_TEMPLATE = """You are helping build a golden test set for evaluating a retrieval system.

    Query: "{query}"

    Below are the top-{top_k} search results returned for this query. Each is a QA pair
    extracted from an interview transcript.

    {candidates}

    For each candidate, judge whether it DIRECTLY and SUBSTANTIVELY answers the query.

    Classify each candidate id into exactly one of:
    - "relevant_ids": the answer content directly and clearly answers the query
    - (omit entirely if irrelevant — don't list irrelevant ids anywhere)

    Be strict about "relevant_ids" — only use it when the answer would genuinely satisfy
    someone asking this exact query. Don't force a match if nothing qualifies.
    """


class LabelResult(BaseModel):
    question: str = Field(description="The question you are answering.")
    relevant_ids: list[str] = Field(description="The id of the answer that directly and clearly answers the query")


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
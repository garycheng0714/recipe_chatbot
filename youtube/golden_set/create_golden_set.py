import asyncio
from typing import Sequence
from uuid import UUID

from pydantic import TypeAdapter
from pydantic_ai import Agent
from sqlalchemy import select

from app.agent.task_processor import TaskProcessor
from app.database import AsyncSessionLocal
from app.repositories.yt_repository import YtRepository
from youtube.domain.models.models import Chunk
from youtube.prompt.section_question_generator import SectionQuestionContent, SectionQuestionGeneratorPrompt, \
    SectionQuestionOutput


def format_chunks_for_prompt(chunks: list[dict[str, str]]) -> str:
    return "\n\n".join(
        f"[chunk_id: {c['chunk_id']}]\n{c['text']}\n[/chunk_id: {c['chunk_id']}]"
        for c in chunks
    )


async def fetch_chunks_by_section(section_id: UUID) -> Sequence[Chunk]:
    async with AsyncSessionLocal() as session:
        return await YtRepository().fetch_chunks_by_section_id(session, section_id)


if __name__ == "__main__":
    async def main():
        yt = YtRepository()

        uuids = [UUID('4294aab7-a13f-5e06-9002-c9d2a6324e32')]

        async with AsyncSessionLocal() as session:
            result = await yt.fetch_current_artifacts(session=session, stage="transcript normalize", uuids=uuids)
            sections = [str(r.output) for r in result]


        tasks = [fetch_chunks_by_section(s) for s in uuids]

        chunks_result = await asyncio.gather(*tasks)

        contents = [
            SectionQuestionContent(
                section=section,
                chunks=format_chunks_for_prompt([
                    {
                        "chunk_id": str(chunk.id),
                        "text": chunk.answer
                    }
                    for chunk in chunks
                ])
            )
            for section, chunks in zip(sections, chunks_result)
        ]

        prompts = [SectionQuestionGeneratorPrompt.render(c) for c in contents]


        agent = Agent(
            model='gemini-2.5-flash',
            output_type=SectionQuestionOutput
        )

        processor = TaskProcessor(agent=agent)

        result = await processor.process_all(prompts)

        adapter = TypeAdapter(list[SectionQuestionOutput])

        with open("gemini_2.5_flash_golden_set.json", "w", encoding="utf-8") as f:
            f.write(adapter.dump_json(result, indent=2).decode())

    asyncio.run(main())

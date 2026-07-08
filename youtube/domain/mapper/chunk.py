from youtube.domain.models.models import Chunk
from youtube.domain.qa_pair_result import QAPairResult


class ChunkMapper:
    @staticmethod
    def from_qa_pairs(pair: QAPairResult, speaker: str) -> list[Chunk]:
        chunks: list[Chunk] = []

        for r in pair.results:
            chunks.append(
                Chunk(
                    section_id=pair.section_id,
                    llm_artifact_id=pair.id,
                    question=r.question,
                    answer=r.answer,
                    topic=r.topic,
                    speaker=speaker,
                    embedding_text=f"""
Question:
{r.question}

Answer:
{r.answer}
""".lstrip()
                )
            )

        return chunks
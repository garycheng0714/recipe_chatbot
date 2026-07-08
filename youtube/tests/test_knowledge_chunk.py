import uuid

from youtube.domain.knowledge_chunk import KnowledgeChunk
from youtube.domain.models.models import Chunk


def test_knowledge_chunk():
    id = uuid.uuid4()
    section_id = uuid.uuid4()

    chunk = Chunk(
            id=id,
            section_id=section_id,
            question="question",
            answer="answers",
            embedding_text="text",
            topic="topic",
            speaker="speaker"
        )

    expected_payload = {
        "question": "question",
        "answer": "answers",
        "topic": "topic",
        "speaker": "speaker",
        "section_id": section_id
    }

    chunk_model = KnowledgeChunk.model_validate(chunk)

    assert chunk_model.get_point_id() == str(chunk.id)
    assert chunk_model.to_embedding_text() == "text"
    assert chunk_model.get_payload() == expected_payload

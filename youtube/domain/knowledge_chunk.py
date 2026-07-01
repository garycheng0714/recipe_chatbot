from uuid import UUID

from pydantic import ConfigDict, BaseModel


class KnowledgeChunk(BaseModel):
    id: UUID
    question: str
    answer: str
    embedding_text: str
    topic: str
    speaker: str

    model_config = ConfigDict(from_attributes=True)

    def to_embedding_text(self) -> str:
        return self.embedding_text

    def get_payload(self) -> dict:
        return {
            "question": self.question,
            "answer": self.answer,
            "topic": self.topic,
            "speaker": self.speaker,
        }

    def get_point_id(self) -> str:
        return str(self.id)
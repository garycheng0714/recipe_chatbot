from uuid import UUID

from youtube.domain.models.models import LlmArtifacts


class LLMArtifactMapper:
    @staticmethod
    def from_output(section_id: UUID, stage: str, output: dict | str) -> LlmArtifacts:
        return LlmArtifacts(
            section_id=section_id,
            stage=stage,
            output=output,
            is_current=True
        )
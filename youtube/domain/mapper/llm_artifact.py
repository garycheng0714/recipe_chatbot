from uuid import UUID

from youtube.domain.models.llm_artifact import LlmArtifacts


class LLMArtifactMapper:
    @staticmethod
    def from_output(section_id: UUID, output: dict) -> LlmArtifacts:
        return LlmArtifacts(
            section_id=section_id,
            stage="transcript normalize",
            output=output,
            is_current=True
        )
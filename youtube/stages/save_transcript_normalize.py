from app.database import AsyncSessionLocal
from app.repositories.yt_repository import YtRepository
from youtube.domain.mapper.llm_artifact import LLMArtifactMapper
from youtube.domain.video_document import VideoDocument
from youtube.ids import get_section_id
from youtube.stages.base_stage import Stage


class SaveTranscriptNormalize(Stage):
    def __init__(self, repository: YtRepository, session_factory = AsyncSessionLocal):
        self.repository = repository
        self.session_factory = session_factory

    async def run(self, document: VideoDocument) -> VideoDocument:

        cleaned_text_dicts = [
            ch.cleaned_content.model_dump()
            for ch in document.chapters
            if ch.cleaned_content is not None
        ]

        artifact_models = [
            LLMArtifactMapper.from_output(
                get_section_id(document.id, idx),
                text_dict
            )
            for idx, text_dict in enumerate(cleaned_text_dicts)
        ]

        async with self.session_factory() as session:
            async with session.begin():
                await self.repository.insert_bulk_llm_artifact(session, artifact_models)

        return document
from app.database import AsyncSessionLocal
from app.repositories.yt_repository import YtRepository
from youtube.domain.mapper.llm_artifact import LLMArtifactMapper
from youtube.domain.video_document import VideoDocument
from youtube.stages.base_stage import Stage


class SaveSpeakerDiarization(Stage):
    def __init__(self, repository: YtRepository, session_factory = AsyncSessionLocal):
        self.repository = repository
        self.session_factory = session_factory

    async def run(self, document: VideoDocument) -> VideoDocument:

        chapters = [
            ch
            for ch in document.chapters
            if ch.speaker_diarization is not None
        ]

        if not chapters:
            return document

        artifact_models = [
            LLMArtifactMapper.from_output(
                section_id=ch.id,
                stage="speaker diarization",
                output=ch.speaker_diarization.model_dump(),
            )
            for ch in chapters
        ]

        async with self.session_factory() as session:
            async with session.begin():
                await self.repository.insert_bulk_llm_artifact(session, artifact_models)

        return document
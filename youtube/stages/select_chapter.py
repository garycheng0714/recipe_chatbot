from uuid import UUID

from youtube.domain.video_document import VideoDocument
from youtube.stages.base_stage import Stage


class SelectChapterStage(Stage):
    def __init__(self, filter_chapter_ids: list[UUID]):
        self.filter_ids = filter_chapter_ids

    async def run(self, document: VideoDocument) -> VideoDocument:
        chapters = []

        for ch in document.chapters:
            if ch.id in self.filter_ids:
                chapters.append(ch)

        document.chapters = chapters

        return document
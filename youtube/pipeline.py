import asyncio

from app.repositories.yt_repository import YtRepository
from web_crawler.requester import HttpxRequester
from youtube.domain.video_document import VideoDocument
from youtube.stages.base_stage import Stage
from youtube.stages.fetch_video import FetchVideoTransformer
from youtube.stages.save_raw_data import SaveRawData
from youtube.stages.transcript_segmenter import TranscriptSegmenter
from youtube.video import YouTubeVideo


class Pipeline:
    def __init__(self, stages: list[Stage]):
        self.stages = stages

    async def run(self, context: VideoDocument):
        for stage in self.stages:
            context = await stage.run(context)
        return context


async def main():
    async with HttpxRequester() as requester:
        pipeline = Pipeline([
            FetchVideoTransformer(yt=YouTubeVideo(requester)),
            TranscriptSegmenter(),
            SaveRawData(repository=YtRepository())
        ])

        context = VideoDocument(id="7E6TNeoOC3Y")

        result = await pipeline.run(context)
        print(result)


if __name__ == '__main__':
    asyncio.run(main())
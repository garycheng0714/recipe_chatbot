from youtube.domain.transcript import SegmenterPayload
from youtube.domain.video import ChapterContent, VideoInfo
from youtube.transformers.base import Transformer


class TranscriptSegmenter(Transformer[SegmenterPayload, VideoInfo]):
    def transform(self, data: SegmenterPayload) -> VideoInfo:
        video = data.video
        chapters = video.chapters_descriptions
        transcripts = data.transcripts

        chapter_dict = {ch.title: [] for ch in chapters}

        for sub in transcripts:
            for ch in reversed(chapters):
                if sub.start >= ch.timestamp:
                    chapter_dict[ch.title].append(sub.text)
                    break

        video.chapters_contents = [
            ChapterContent(title=title, content=" ".join(content))
            for title, content in chapter_dict.items()
        ]

        return video
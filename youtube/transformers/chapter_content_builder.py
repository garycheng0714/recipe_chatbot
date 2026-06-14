from youtube.domain.chapter_content import ChapterPayload, ChapterContent
from youtube.transformers.base import Transformer


class ChapterContentBuilder(Transformer[ChapterPayload, list[ChapterContent]]):
    def transform(self, data: ChapterPayload) -> list[ChapterContent]:
        chapters = data.chapters
        transcripts = data.transcripts

        chapter_dict = {ch.title: [] for ch in chapters}

        for sub in transcripts:
            for ch in reversed(chapters):
                if sub.start >= ch.timestamp:
                    chapter_dict[ch.title].append(sub.text)
                    break

        return [
            ChapterContent(title=title, content=" ".join(content))
            for title, content in chapter_dict.items()
        ]
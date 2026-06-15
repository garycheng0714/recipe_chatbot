from youtube.domain.video_document import Chapter, VideoDocument


class TranscriptSegmenter:

    async def run(self, document: VideoDocument) -> VideoDocument:
        chapters = document.description
        transcripts = document.transcripts

        chapter_dict = {ch.title: [] for ch in chapters}

        for sub in transcripts:
            for ch in reversed(chapters):
                if sub.start >= ch.start_time:
                    chapter_dict[ch.title].append(sub.text)
                    break

        document.chapters = [
            Chapter(title=title, content=" ".join(content))
            for title, content in chapter_dict.items()
        ]

        return document
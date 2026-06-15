from youtube.domain.video_document import Chapter, VideoDocument


class TranscriptSegmenter:

    async def run(self, document: VideoDocument) -> VideoDocument:
        chapters = document.description
        transcripts = document.transcripts

        # 遇到同樣標題會少章節，故用 start_time 當 key
        chapter_dict = {str(ch.start_time): [] for ch in chapters}

        for sub in transcripts:
            for ch in reversed(chapters):
                if sub.start >= ch.start_time:
                    chapter_dict[str(ch.start_time)].append(sub.text)
                    break

        document.chapters = [
            Chapter(title=ch.title, content=" ".join(chapter_dict[key]))
            for ch, key in zip(chapters, chapter_dict.keys())
        ]

        return document
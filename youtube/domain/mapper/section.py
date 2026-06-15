from youtube.domain.models import Section
from youtube.domain.video_document import VideoDocument
from youtube.ids import get_source_id, get_section_id


class SectionMapper:
    @staticmethod
    def from_document(video: VideoDocument) -> list[Section]:
        sections: list[Section] = []

        if len(video.chapters) != len(video.description):
            return sections

        source_id = get_source_id(video.url)

        for idx, (ch, description) in enumerate(zip(video.chapters, video.description)):
            sections.append(
                Section(
                    id=get_section_id(source_id, idx),
                    source_id=source_id,
                    title=ch.title,
                    order_index=idx,
                    raw_content=ch.content,
                    start_time=description.start_time
                )
            )

        return sections
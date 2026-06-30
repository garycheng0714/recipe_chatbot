from uuid import UUID

import pytest

from youtube.domain.video_document import VideoDocument, Chapter
from youtube.stages.select_chapter import SelectChapterStage


@pytest.mark.asyncio
async def test_select_chapter():
    ch_id_1 = UUID('0d72446b-cebb-5eef-a81d-19b9604b4eaf')
    ch_id_2 = UUID('0d72446b-cebb-5eef-a81d-19b9604b4eff')

    video = VideoDocument(
        chapters=[
            Chapter(
                id=ch_id_1,
                title="Chapter 1",
                content="Content 1",
            ),
            Chapter(
                id=ch_id_2,
                title="Chapter 2",
                content="Content 2",
            )
        ]
    )

    stage = SelectChapterStage([ch_id_1])

    result = await stage.run(video)

    assert len(result.chapters) == 1
    assert result.chapters[0].id == ch_id_1


@pytest.mark.asyncio
async def test_select_chapter():
    ch_id_1 = UUID('0d72446b-cebb-5eef-a81d-19b9604b4eaf')
    ch_id_2 = UUID('0d72446b-cebb-5eef-a81d-19b9604b4eff')

    video = VideoDocument(
        chapters=[
            Chapter(
                id=ch_id_1,
                title="Chapter 1",
                content="Content 1",
            ),
            Chapter(
                id=ch_id_2,
                title="Chapter 2",
                content="Content 2",
            )
        ]
    )

    stage = SelectChapterStage([ch_id_1])

    result = await stage.run(video)

    assert len(result.chapters) == 1
    assert result.chapters[0].id == ch_id_1


@pytest.mark.asyncio
async def test_select_chapter_then_no_chapter_selected():
    ch_id_1 = UUID('0d72446b-cebb-5eef-a81d-19b9604b4eaf')
    ch_id_2 = UUID('0d72446b-cebb-5eef-a81d-19b9604b4eff')
    ch_id_3 = UUID('0d72446b-cebb-5eef-a81d-19b9604b4ebf')

    video = VideoDocument(
        chapters=[
            Chapter(
                id=ch_id_1,
                title="Chapter 1",
                content="Content 1",
            ),
            Chapter(
                id=ch_id_2,
                title="Chapter 2",
                content="Content 2",
            )
        ]
    )

    stage = SelectChapterStage([ch_id_3])

    result = await stage.run(video)

    assert len(result.chapters) == 0

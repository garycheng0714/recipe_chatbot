import pytest
import pytest_asyncio
from sqlalchemy import delete

from app.repositories.yt_repository import YtRepository
from youtube.domain.models.models import Source, Section, Chunk, ChunkTranslation
from youtube.domain.video_document import VideoDocument
from youtube.ids import get_source_id, get_section_id
from youtube.stages.fetch_video_from_db import FetchVideoFromDB


@pytest.fixture
def uuid():
    return get_source_id("https://example-video.com")


@pytest_asyncio.fixture(loop_scope="session")
async def clean_db(session):
    yield  # 測試執行
    # 測試結束後清理
    async with session.begin():
        await session.execute(delete(ChunkTranslation))
        await session.execute(delete(Chunk))
        await session.execute(delete(Section))
        await session.execute(delete(Source))


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_fetch_video_from_db(uuid, session_factory, clean_db):

    async with session_factory() as async_session:
        async with async_session.begin():
            repo = YtRepository()
            video = Source(
                id=uuid,
                type="youtube",
                video_id="123",
                title="測試影片",
                url="https://example-video.com",
                language="en",
                sections=[
                    Section(
                        id=get_section_id(uuid, 0),
                        source_id=uuid,
                        title="章節一",
                        order_index=0,
                        raw_content="內容一",
                    ),
                    Section(
                        id=get_section_id(uuid, 1),
                        source_id=uuid,
                        title="章節二",
                        order_index=1,
                        raw_content="內容二",
                    )
                ]
            )

            # 執行寫入
            async_session.add(video)

    # 驗證是否真的寫入資料庫
    stage = FetchVideoFromDB(repo, session_factory)
    context = VideoDocument(url="https://example-video.com")

    video = await stage.run(context)

    assert video.title == "測試影片"
    assert video.url == "https://example-video.com"
    assert video.video_id == "123"

    assert len(video.chapters) == 2

    chapter = video.chapters[0]
    assert chapter.id == get_section_id(uuid, 0)
    assert chapter.title == "章節一"
    assert chapter.content == "內容一"



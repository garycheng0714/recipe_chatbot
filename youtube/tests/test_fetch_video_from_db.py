import pytest
import pytest_asyncio
from sqlalchemy import delete

from app.repositories.yt_repository import YtRepository
from youtube.domain.models import Source, Section, Chunk, ChunkTranslation
from youtube.domain.video_document import VideoDocument
from youtube.ids import get_source_id
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


async def test_fetch_video_from_db(uuid, session_factory):

    async with session_factory() as async_session:
        async with async_session.begin():
            repo = YtRepository()
            video = Source(id=uuid, type="youtube", title="測試影片", url="https://example-video.com", language="en")

            # 執行寫入
            await repo.insert(async_session, video)

    # 驗證是否真的寫入資料庫
    stage = FetchVideoFromDB(repo, session_factory)
    video = VideoDocument(url="https://example-video.com")

    result = await stage.run(video)

    assert result.title == "測試影片"
    assert result.url == "https://example-video.com"



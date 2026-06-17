import pytest

from app.repositories.yt_repository import YtRepository
from youtube.domain.models import Source, Section
from youtube.ids import get_source_id, get_section_id


@pytest.fixture
def uuid():
    return get_source_id("vid_001")

pytestmark = pytest.mark.asyncio(loop_scope="session")

async def test_insert_video_success(session, uuid):
    repo = YtRepository()
    video = Source(id=uuid, type="youtube", video_id="123", title="測試影片", url="https://example.com", language="en")

    # 執行寫入
    await repo.insert(session, video)
    await session.flush()

    # 驗證是否真的寫入資料庫
    result = await repo.fetch(Source, session, [uuid])
    assert len(result) == 1

    video = result[0]
    assert video.title == "測試影片"
    assert video.url == "https://example.com"


async def test_fetch_video_fail(session):
    repo = YtRepository()
    uuid = get_source_id("vid_001")

    # 驗證是否真的寫入資料庫
    result = await repo.fetch(Source, session, [uuid])
    assert len(result) == 0


async def test_insert_video_on_conflict_do_nothing(session, uuid):
    repo = YtRepository()
    video1 = Source(id=uuid, type="youtube", video_id="123", title="原本的標題", url="https://example.com", language="en")
    video2 = Source(id=uuid, type="youtube", video_id="123", title="衝突的標題", url="https://example.com", language="en")

    # 寫入第一筆
    await repo.insert(session, video1)
    # 寫入第二筆 (同 ID)
    await repo.insert(session, video2)
    await session.flush()

    # 驗證 on_conflict_do_nothing 是否生效 (應該保留第一筆的資料)
    result = await repo.fetch(Source, session, [uuid])
    assert len(result) == 1

    video = result[0]
    assert video.title == "原本的標題"  # 沒有被第二筆覆蓋


async def test_insert_chapter_success(session, uuid):
    repo = YtRepository()
    chapter_id = get_section_id(uuid, 0)

    video = Source(
        id=uuid,
        type="youtube",
        video_id="123",
        title="測試影片",
        url="https://example.com",
        language="en"
    )

    chapter = Section(
        id=chapter_id,
        source_id=uuid,
        title="第一章",
        order_index=0,
        raw_content="內容",
        start_time=10.5
    )

    # 執行寫入
    await repo.insert(session, video)
    await repo.insert(session, chapter)
    await session.flush()

    # 驗證結果
    result = await repo.fetch(Section, session, [chapter_id])
    assert len(result) == 1

    chapter = result[0]
    assert chapter.title == "第一章"
    assert chapter.start_time == 10.5


async def test_insert_bulk_chapter_success(session, uuid):
    repo = YtRepository()

    video = Source(
        id=uuid,
        type="youtube",
        video_id="123",
        title="測試影片",
        url="https://example.com",
        language="en"
    )

    chapter1_id = get_section_id(uuid, 0)

    chapter1 = Section(
        id=chapter1_id,
        source_id=uuid,
        title="第一章",
        order_index=0,
        raw_content="內容",
        start_time=0
    )

    chapter2_id = get_section_id(uuid, 1)

    chapter2 = Section(
        id=chapter2_id,
        source_id=uuid,
        title="第二章",
        order_index=1,
        raw_content="內容二",
        start_time=10
    )

    # 執行寫入
    await repo.insert(session, video)
    await repo.insert_bulk(session, [chapter1, chapter2])
    await session.flush()

    # 驗證結果
    result = await repo.fetch(Section, session, [chapter1_id, chapter2_id])
    assert len(result) == 2

    chapter = result[0]
    assert chapter.title == "第一章"
    assert chapter.raw_content == "內容"
    assert chapter.start_time == 0

    chapter = result[1]
    assert chapter.title == "第二章"
    assert chapter.raw_content == "內容二"
    assert chapter.start_time == 10


async def test_insert_duplicated_chapter_then_one_result(session, uuid):
    repo = YtRepository()

    video = Source(
        id=uuid,
        type="youtube",
        video_id="123",
        title="測試影片",
        url="https://example.com",
        language="en"
    )

    chapter1_id = get_section_id(uuid, 0)

    chapter1 = Section(
        id=chapter1_id,
        source_id=uuid,
        title="第一章",
        order_index=0,
        raw_content="內容",
        start_time=0
    )

    chapter2 = Section(
        id=chapter1_id,
        source_id=uuid,
        title="第二章",
        order_index=1,
        raw_content="內容二",
        start_time=10
    )

    # 執行寫入
    await repo.insert(session, video)
    await repo.insert_bulk(session, [chapter1, chapter2])
    await session.flush()

    # 驗證結果
    result = await repo.fetch(Section, session, [chapter1_id])
    assert len(result) == 1

    chapter = result[0]
    assert chapter.title == "第一章"
    assert chapter.raw_content == "內容"
    assert chapter.start_time == 0
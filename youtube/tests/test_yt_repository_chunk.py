import pytest
from sqlalchemy import select

from app.repositories.yt_repository import YtRepository
from youtube.domain.models.models import LlmArtifacts, Chunk, Source, Section
from youtube.ids import get_source_id, get_section_id


@pytest.fixture
def uuid():
    return get_source_id("https://www.google.com")

@pytest.fixture
def artifacts():
    return [
        LlmArtifacts(
            section_id=get_section_id(get_source_id("https://www.google.com"), 0),
            stage="transcript normalize",
            output="123",
            is_current=True
        ),
        LlmArtifacts(
            section_id=get_section_id(get_source_id("https://www.google.com"), 1),
            stage="transcript normalize",
            output="456",
            is_current=True
        )
    ]

# 1. 建立 Chunk 的測試資料 Fixture
@pytest.fixture
def chunks(uuid):
    # 假設 get_section_id 是你用來產生 UUID 的 helper function
    section_id_1 = get_section_id(uuid, 0)
    section_id_2 = get_section_id(uuid, 1)

    return [
        Chunk(
            section_id=section_id_1,
            question="什麼是測試 1？",
            answer="這是測試回答 1",
            embedding_text=f"Question:\n什麼是測試 1？\n\nAnswer:\n這是測試回答 1",
            topic = "單元測試"
        ),
        Chunk(
            section_id=section_id_2,
            question="什麼是測試 2？",
            answer="這是測試回答 2",
            embedding_text = f"Question:\n什麼是測試 2？\n\nAnswer:\n這是測試回答 2",
            topic = "整合測試"
        )
    ]


# 2. 設定 pytest 標記
pytestmark = pytest.mark.asyncio(loop_scope="session")

    # 3. 測試本體
async def test_insert_bulk_chunk(chunks, session, uuid, artifacts):
    repo = YtRepository()

    # 建立上游依賴：Source (影片)
    video = Source(
        id=uuid,
        type="youtube",
        video_id="123",
        title="測試影片",
        url="https://example.com",
        language="en"
    )

    # 建立上游依賴：Section (章節)
    chapter = Section(
        id=get_section_id(uuid, 0),
        source_id=uuid,
        title="第一章",
        order_index=0,
        raw_content="內容",
        start_time=10.5
    )

    chapter2 = Section(
        id=get_section_id(uuid, 1),
        source_id=uuid,
        title="第二章",
        order_index=1,
        raw_content="內容2",
        start_time=20.5
    )

    # 先寫入必要的前置資料
    await repo.insert(session, video)
    await repo.insert_bulk_section(session, [chapter, chapter2])
    await repo.insert_bulk_llm_artifact(session, artifacts)
    await session.flush()  # 確保資料庫此時已知悉 Section 的存在

    # 🚀 執行你要測試的 insert_bulk_chunk 方法
    # 假設這個方法封裝在你的 repo 物件中，若否，請改為：await insert_bulk_chunk(session, chunks)
    await repo.insert_bulk_chunk(session, chunks)
    await session.flush()

    # 4. 驗證資料是否正確寫入
    section_ids = [get_section_id(uuid, 0), get_section_id(uuid, 1)]

    # 從資料庫重新查出剛剛寫入的 Chunks 進行斷言 (Assert)
    stmt = (
        select(Chunk)
            .where(Chunk.section_id.in_(section_ids))
            .order_by(Chunk.question)
    )

    result = (await session.execute(stmt)).scalars().all()

    # 驗證數量
    assert len(result) == 2

    # 驗證第一筆資料欄位
    assert result[0].question == "什麼是測試 1？"
    assert result[0].answer == "這是測試回答 1"
    assert result[0].topic == "單元測試"
    assert result[0].id is not None  # 驗證是否有自動生成 uuid
    assert result[0].created_at is not None  # 驗證 server_default 觸發成功

    # 驗證第二筆資料欄位
    assert result[1].question == "什麼是測試 2？"
    assert result[1].answer == "這是測試回答 2"
    assert result[1].topic == "整合測試"
    assert result[1].id is not None


async def test_insert_bulk_chunk_twice(chunks, session, uuid, artifacts):
    repo = YtRepository()

    # 建立上游依賴：Source (影片)
    video = Source(
        id=uuid,
        type="youtube",
        video_id="123",
        title="測試影片",
        url="https://example.com",
        language="en"
    )

    # 建立上游依賴：Section (章節)
    chapter = Section(
        id=get_section_id(uuid, 0),
        source_id=uuid,
        title="第一章",
        order_index=0,
        raw_content="內容",
        start_time=10.5
    )

    chapter2 = Section(
        id=get_section_id(uuid, 1),
        source_id=uuid,
        title="第二章",
        order_index=1,
        raw_content="內容2",
        start_time=20.5
    )

    # 先寫入必要的前置資料
    await repo.insert(session, video)
    await repo.insert_bulk_section(session, [chapter, chapter2])
    await repo.insert_bulk_llm_artifact(session, artifacts)
    await session.flush()  # 確保資料庫此時已知悉 Section 的存在

    # 🚀 執行你要測試的 insert_bulk_chunk 方法
    # 假設這個方法封裝在你的 repo 物件中，若否，請改為：await insert_bulk_chunk(session, chunks)
    await repo.insert_bulk_chunk(session, chunks)
    await session.flush()

    await repo.insert_bulk_chunk(session, chunks)
    await session.flush()

    # 4. 驗證資料是否正確寫入
    section_ids = [get_section_id(uuid, 0), get_section_id(uuid, 1)]

    # 從資料庫重新查出剛剛寫入的 Chunks 進行斷言 (Assert)
    stmt = (
        select(Chunk)
            .where(Chunk.section_id.in_(section_ids))
            .order_by(Chunk.question)
    )

    result = (await session.execute(stmt)).scalars().all()

    # 驗證數量
    assert len(result) == 2
import pytest

from app.repositories.yt_repository import YtRepository
from youtube.domain.models.models import LlmArtifacts
from youtube.domain.models.models import Source, Section
from youtube.domain.speaker_diarization_result import SpeakerDiarizationResult, QA
from youtube.ids import get_source_id, get_section_id


@pytest.fixture
def uuid():
    return get_source_id("vid_001")

pytestmark = pytest.mark.asyncio(loop_scope="session")

async def test_insert_video_success(session, uuid):
    repo = YtRepository()
    video = Source(
        id=uuid,
        type="youtube",
        video_id="123",
        author="AA",
        speaker="BB",
        title="測試影片",
        url="https://example.com",
        language="en"
    )

    # 執行寫入
    await repo.insert(session, video)
    await session.flush()

    # 驗證是否真的寫入資料庫
    result = await repo.fetch(Source, session, [uuid])
    assert len(result) == 1

    video = result[0]
    assert video.title == "測試影片"
    assert video.url == "https://example.com"
    assert video.author == "AA"
    assert video.speaker == "BB"


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
    await repo.insert_bulk_section(session, [chapter1, chapter2])
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
    await repo.insert_bulk_section(session, [chapter1, chapter2])
    await session.flush()

    # 驗證結果
    result = await repo.fetch(Section, session, [chapter1_id])
    assert len(result) == 1

    chapter = result[0]
    assert chapter.title == "第一章"
    assert chapter.raw_content == "內容"
    assert chapter.start_time == 0


async def test_get_video_by_uuid_success(session, uuid):
    repo = YtRepository()

    # 1. 建立並寫入 Source (影片) 基礎資料
    video = Source(
        id=uuid,
        type="youtube",
        video_id="123",
        title="測試影片",
        url="https://example.com",
        language="en"
    )
    await repo.insert(session, video)

    # 2. 建立並寫入複數個 Section (章節)
    section_id_0 = get_section_id(uuid, 0)
    section_id_1 = get_section_id(uuid, 1)

    chapter1 = Section(
        id=section_id_0,
        source_id=uuid,
        title="第一章",
        order_index=0,
        raw_content="內容1",
        start_time=0
    )
    chapter2 = Section(
        id=section_id_1,
        source_id=uuid,
        title="第二章",
        order_index=1,
        raw_content="內容二",
        start_time=10
    )
    await repo.insert_bulk_section(session, [chapter1, chapter2])

    # 3. 建立並寫入 LlmArtifacts (包含不同 stage 與不同 section 的對應資料)
    artifacts = [
        # Section 0 的產物
        LlmArtifacts(
            section_id=section_id_0,
            stage="transcript normalize",
            is_current=True,
            output="第一章正規化文字"
        ),
        LlmArtifacts(
            section_id=section_id_0,
            stage="speaker diarization",
            is_current=True,
            output={"conversation": [{"speaker": "interviewer", "intent": "question", "text": "講話A"}]}
        ),
        # Section 1 的產物
        LlmArtifacts(
            section_id=section_id_1,
            stage="transcript normalize",
            is_current=True,
            output="第二章正規化文字"
        ),
        LlmArtifacts(
            section_id=section_id_1,
            stage="speaker diarization",
            is_current=True,
            output={"conversation": [{"speaker": "interviewer", "intent": "question", "text": "講話B"}]}
        ),
        # 雜訊資料：非 current 的產物 (預期不應該被掛載上去)
        LlmArtifacts(
            section_id=section_id_0,
            stage="transcript normalize",
            is_current=False,
            output="舊的錯誤文字"
        )
    ]
    await repo.insert_bulk_llm_artifact(session, artifacts)

    # 確保所有測試資料都寫入資料庫並清除 session 快取，以驗證真正的 SQL 查詢行為
    await session.flush()
    session.expire_all()

    # 4. 執行待測函式
    result_source = await repo.get_video_by_uuid(session, uuid)

    # 5. 驗證結果
    assert result_source is not None
    assert result_source.id == uuid
    assert result_source.title == "測試影片"

    # 驗證 sections 是否有透過 selectinload 正確加載且數量正確
    assert len(result_source.sections) == 2

    # 將 sections 轉換成 dict 以方便透過 ID 進行精準斷言
    sections_dict = {s.id: s for s in result_source.sections}

    # 驗證第一章 (section_id_0) 的動態屬性掛載
    s0 = sections_dict[section_id_0]
    assert s0.title == "第一章"
    assert s0.cleaned_content == "第一章正規化文字"
    assert s0.speaker_diarization.conversation == [QA(speaker="interviewer", intent="question", text="講話A")]

    # 驗證第二章 (section_id_1) 的動態屬性掛載
    s1 = sections_dict[section_id_1]
    assert s1.title == "第二章"
    assert s1.cleaned_content == "第二章正規化文字"
    assert s1.speaker_diarization.conversation == [QA(speaker="interviewer", intent="question", text="講話B")]


async def test_get_video_by_uuid_not_found(session, uuid):
    repo = YtRepository()

    # 測試傳入不存在的 UUID 時，函式是否能正確回傳 None
    non_existent_id = uuid

    result = await repo.get_video_by_uuid(session, non_existent_id)
    assert result is None
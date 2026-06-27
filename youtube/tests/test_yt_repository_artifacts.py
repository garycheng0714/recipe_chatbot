import pytest

from app.repositories.yt_repository import YtRepository
from youtube.domain.models.llm_artifact import LlmArtifacts
from youtube.domain.models.models import Source, Section
from youtube.ids import get_section_id, get_source_id


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

@pytest.fixture
def single_artifact():
    return LlmArtifacts(
            section_id=get_section_id(get_source_id("https://www.google.com"), 0),
            stage="transcript normalize",
            output="789",
            is_current=True
        )


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_insert_llm_artifact(artifacts, session, uuid):
    repo = YtRepository()

    video = Source(
        id=uuid,
        type="youtube",
        video_id="123",
        title="測試影片",
        url="https://example.com",
        language="en"
    )

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

    # 執行寫入
    await repo.insert(session, video)
    await repo.insert_bulk_section(session, [chapter, chapter2])

    await repo.insert_bulk_llm_artifact(session, artifacts)
    await session.flush()

    section_ids = [
        get_section_id(uuid, 0),
        get_section_id(uuid, 1),
    ]

    result = await repo.fetch_artifacts(session, section_ids)

    assert len(result) == 2

    assert result[0].output == "123"
    assert result[0].id is not None

    assert result[1].output == "456"
    assert result[1].id is not None


async def test_insert_llm_artifact_then_update_the_is_current_status(single_artifact, artifacts, session, uuid):
    repo = YtRepository()

    video = Source(
        id=uuid,
        type="youtube",
        video_id="123",
        title="測試影片",
        url="https://example.com",
        language="en"
    )

    chapter = Section(
        id=get_section_id(uuid, 0),
        source_id=uuid,
        title="第一章",
        order_index=0,
        raw_content="內容",
        start_time=10.5
    )

    # 執行寫入
    await repo.insert(session, video)
    await repo.insert_bulk_section(session, [chapter])

    await repo.insert_bulk_llm_artifact(session, artifacts[:1])
    await repo.insert_bulk_llm_artifact(session, [single_artifact])
    await session.flush()

    section_ids = [
        get_section_id(uuid, 0)
    ]

    result = await repo.fetch_artifacts(session, section_ids)

    assert len(result) == 2
    assert result[0].is_current == False
    assert result[0].output == "123"
    assert result[1].is_current == True
    assert result[1].output == "789"


async def test_fetch_current_artifacts(session, uuid):
    repo = YtRepository()

    # 1. 建立測試所需的基礎資料 (Video 與 Sections)
    video = Source(
        id=uuid,
        type="youtube",
        video_id="123",
        title="測試影片",
        url="https://example.com",
        language="en"
    )

    section_id_1 = get_section_id(uuid, 0)
    section_id_2 = get_section_id(uuid, 1)
    section_id_3 = get_section_id(uuid, 2)

    chapter1 = Section(
        id=section_id_1,
        source_id=uuid,
        title="第一章",
        order_index=0,
        raw_content="內容1",
        start_time=10.5
    )
    chapter2 = Section(
        id=section_id_2,
        source_id=uuid,
        title="第二章",
        order_index=1,
        raw_content="內容2",
        start_time=20.5
    )
    chapter3 = Section(
        id=section_id_3,
        source_id=uuid,
        title="第二章",
        order_index=2,
        raw_content="內容2",
        start_time=20.5
    )

    await repo.insert(session, video)
    await repo.insert_bulk_section(session, [chapter1, chapter2, chapter3])

    # 2. 建立各種狀況的 LlmArtifacts 來測試篩選邏輯
    stage_target = "summary"
    stage_other = "translation"

    artifacts = [
        # 條件完全符合 1
        LlmArtifacts(
            section_id=section_id_1,
            stage=stage_target,
            is_current=True,
            output={"text": "符合條件1"}
        ),
        # 條件完全符合 2
        LlmArtifacts(
            section_id=section_id_2,
            stage=stage_target,
            is_current=True,
            output={"text": "符合條件2"}
        ),
        # 不符合：is_current 為 False
        LlmArtifacts(
            section_id=section_id_1,
            stage=stage_target,
            is_current=False,
            output={"text": "舊的資料"}
        ),
        # 不符合：stage 不對
        LlmArtifacts(
            section_id=section_id_1,
            stage=stage_other,
            is_current=True,
            output={"text": "不同階段的資料"}
        ),
        # 不符合：section_id 不在查詢清單中（假設有第三個 section）
        LlmArtifacts(
            section_id=section_id_3,
            stage=stage_target,
            is_current=True,
            output={"text": "不在查詢 UUID 清單中的資料"}
        )
    ]

    await repo.insert_bulk_llm_artifact(session, artifacts)
    await session.flush()

    # 3. 呼叫待測的受保護 function (_fetch_current_artifacts)
    # 註：在 Python 中測試受保護方法（單底線開頭）可以直接透過實例呼叫
    target_uuids = [section_id_1, section_id_2]
    result = await repo._fetch_current_artifacts(
        session=session,
        stage=stage_target,
        uuids=target_uuids
    )

    # 4. 驗證結果
    # 預期只會查出前 2 筆符合所有條件的資料
    assert len(result) == 2

    assert result[0].id is not None
    assert result[1].id is not None

    # 驗證撈出來的資料內容是否正確
    outputs = [item.output for item in result]
    assert {"text": "符合條件1"} in outputs
    assert {"text": "符合條件2"} in outputs

    # 確保另外 3 筆不符條件的資料沒有被撈出來
    assert {"text": "舊的資料"} not in outputs
    assert {"text": "不同階段的資料"} not in outputs
    assert {"text": "不在查詢 UUID 清單中的資料"} not in outputs
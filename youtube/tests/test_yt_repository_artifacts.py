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
            output={"cleaned_text": "123"},
            is_current=True
        ),
        LlmArtifacts(
            section_id=get_section_id(get_source_id("https://www.google.com"), 1),
            stage="transcript normalize",
            output={"cleaned_text": "456"},
            is_current=True
        )
    ]

@pytest.fixture
def single_artifact():
    return LlmArtifacts(
            section_id=get_section_id(get_source_id("https://www.google.com"), 0),
            stage="transcript normalize",
            output={"cleaned_text": "789"},
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

    assert result[0].output == {"cleaned_text": "123"}
    assert result[1].output == {"cleaned_text": "456"}


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
    assert result[0].output == {"cleaned_text": "123"}
    assert result[1].is_current == True
    assert result[1].output == {"cleaned_text": "789"}



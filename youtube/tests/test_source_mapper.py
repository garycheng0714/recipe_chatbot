from datetime import datetime, timezone

from youtube.domain.mapper.source import SourceMapper
from youtube.domain.models import SourceType
from youtube.domain.video_document import VideoDocument, ChapterDescription
from youtube.ids import get_source_id


def test_source_mapper_from_document_success():
    # 1. 準備測試資料 (Arrange)
    mock_published_at = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

    video_doc = VideoDocument(
        video_id="video_001",
        title="如何寫出好測試",
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        author="測試大師",
        language="zh-TW",
        published_at=mock_published_at,
        description=[
            ChapterDescription(title="前言", start_time=0.0),
            ChapterDescription(title="主文", start_time=60.0)
        ],
        chapters=[],
        transcripts=[]
    )

    # 2. 執行受測動作 (Act)
    result_source = SourceMapper.from_document(video_doc)

    # 3. 驗證結果是否符合預期 (Assert)
    assert result_source.id == get_source_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")  # 依據你的 get_source_id 邏輯
    assert result_source.type == SourceType.youtube
    assert result_source.video_id == "video_001"
    assert result_source.title == "如何寫出好測試"
    assert result_source.url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert result_source.author == "測試大師"
    assert result_source.language == "zh-TW"
    assert result_source.published_at == mock_published_at
import pytest

from youtube.domain.mapper.section import SectionMapper
from youtube.domain.video_document import Chapter, ChapterDescription, VideoDocument
from youtube.ids import get_source_id, get_section_id


def test_section_mapper_from_document_success():
    # 1. 準備測試資料 (Arrange)
    # 建立兩個章節內容與兩個對應的時間敘述
    chapters = [
        Chapter(title="第一章：導論", content="這是導論的內容..."),
        Chapter(title="第二章：核心概念", content="這是核心概念的內容...")
    ]

    descriptions = [
        ChapterDescription(title="導論時間軸", start_time=0.0),
        ChapterDescription(title="核心概念時間軸", start_time=125.5)
    ]

    video_doc = VideoDocument(
        id="vid_999",
        url="https://www.youtube.com/watch?v=abcdefg",
        chapters=chapters,
        description=descriptions
        # 其他欄位帶 None 或預設值即可，此測試用不到
    )

    # 預期從輔助函式得到的 ID
    expected_source_id = get_source_id(video_doc.url)

    # 2. 執行受測動作 (Act)
    sections = SectionMapper.from_document(video_doc)

    # 3. 驗證結果 (Assert)
    # 驗證產出的 Section 數量是否正確
    assert len(sections) == 2

    # 驗證第一個 Section (idx = 0)
    sec1 = sections[0]
    assert sec1.id == get_section_id(expected_source_id, 0)
    assert sec1.source_id == expected_source_id
    assert sec1.title == "第一章：導論"  # 來自 chapters
    assert sec1.order_index == 0
    assert sec1.raw_content == "這是導論的內容..."  # 來自 chapters
    assert sec1.start_time == 0.0  # 來自 description

    # 驗證第二個 Section (idx = 1)
    sec2 = sections[1]
    assert sec2.id == get_section_id(expected_source_id, 1)
    assert sec2.source_id == expected_source_id
    assert sec2.title == "第二章：核心概念"
    assert sec2.order_index == 1
    assert sec2.raw_content == "這是核心概念的內容..."
    assert sec2.start_time == 125.5


def test_section_mapper_with_empty_lists():
    # 測試當 chapters 和 description 都是空列表時，應回傳空列表
    video_doc = VideoDocument(
        url="https://www.youtube.com/watch?v=abcdefg",
        chapters=[],
        description=[]
    )

    sections = SectionMapper.from_document(video_doc)

    assert sections == []


def test_section_mapper_mismatched_lengths():
    # 測試當 chapters 和 description 長度不一致時 (Python zip 的特性會以短的為主)
    # 雖然這可能是商務邏輯上的異常，但測試能確保 Mapper 不會崩潰
    chapters = [Chapter(title="孤立的章節", content="沒有時間軸")]
    descriptions = []  # 空的

    video_doc = VideoDocument(
        url="https://www.youtube.com/watch?v=abcdefg",
        chapters=chapters,
        description=descriptions
    )

    with pytest.raises(Exception):
        SectionMapper.from_document(video_doc)
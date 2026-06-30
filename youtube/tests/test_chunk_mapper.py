import uuid

from youtube.domain.mapper.chunk import ChunkMapper
from youtube.domain.models.models import Chunk
from youtube.domain.qa_pair_result import QAPairResult


def test_from_qa_pairs_success(session):
    # 1. 準備測試資料 (Arrange)
    fake_section_id = uuid.uuid4()

    raw_data = {
        "section_id": fake_section_id,
        "output": [  # 測試 validation_alias 是否能正確解析 'output'
            {
                "question": "什麼是 RAG？",
                "answer": "檢索增強生成技術。",
                "topic": "AI 技術"
            },
            {
                "question": "什麼是 LLM？",
                "answer": "大型語言模型。",
                "topic": "AI 技術"
            }
        ]
    }

    # 建立 Pydantic 模型實例
    qa_pair_result = QAPairResult(**raw_data)

    # 2. 執行被測試的方法 (Act)
    chunks = ChunkMapper.from_qa_pairs(qa_pair_result)

    # 3. 驗證結果是否符合預期 (Assert)
    assert len(chunks) == 2

    # 驗證第一個 Chunk 的內容與格式
    chunk1 = chunks[0]
    assert isinstance(chunk1, Chunk)
    assert chunk1.section_id == fake_section_id
    assert chunk1.question == "什麼是 RAG？"
    assert chunk1.answer == "檢索增強生成技術。"
    assert chunk1.topic == "AI 技術"

    # 驗證 embedding_text 的格式是否與 Mapper 中定義的多行字串一致
    expected_embedding_text_1 = f"""
Question:
什麼是 RAG？

Answer:
檢索增強生成技術。
""".lstrip()
    assert chunk1.embedding_text == expected_embedding_text_1

    # 驗證第二個 Chunk 的內容
    chunk2 = chunks[1]
    assert isinstance(chunk2, Chunk)
    assert chunk2.section_id == fake_section_id
    assert chunk2.question == "什麼是 LLM？"
    assert chunk2.answer == "大型語言模型。"
    assert chunk2.topic == "AI 技術"


def test_from_qa_pairs_empty_results():
    # 測試當結果清單為空時，是否能正確回傳空陣列
    qa_pair_result = QAPairResult(section_id=uuid.uuid4(), results=[])

    chunks = ChunkMapper.from_qa_pairs(qa_pair_result)

    assert chunks == []
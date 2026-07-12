from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from app.domain.chunks import MainChunk, OverviewChunk, InstructionChunk
from app.infrastructure.qdrant.config import RecipeQdrantSetting
from app.repositories import QdrantRepository
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe, Step, Ingredient


@pytest.fixture
def recipe():
    return TastyNoteRecipe(
        id="123",
        name="Test",
        source_url="https://example.com",
        category="tw",
        description="Test",
        quantity="1",
        ingredients=[Ingredient(name="a", amount="1"), Ingredient(name="b", amount="1")],
        steps=[Step(img="jpg", step="a"), Step(img="img", step="b")],
        tags=["jp"],
    )


@pytest.fixture
def recipe_without_ingredients():
    return TastyNoteRecipe(
        id="123",
        name="Test",
        source_url="https://example.com",
        category="tw",
        description="Test",
        steps=[Step(img="jpg", step="a"), Step(img="img", step="b")],
        tags=["jp"],
    )


@pytest.mark.asyncio
async def test_qdr_repository_upsert_main_chunk(recipe):
    client = AsyncMock()
    embed_client = MagicMock()
    embed_client.post = AsyncMock()

    setting = RecipeQdrantSetting()

    repository = QdrantRepository(setting, client, embed_client)

    chunk = MainChunk.from_recipe(recipe)

    with patch.object(repository, "_compute_embeddings", new_callable=AsyncMock) as mock_computer_embeddings:
        mock_computer_embeddings.return_value = [[1, 2, 3]]
        await repository.upsert_recipe(chunk)

        mock_computer_embeddings.assert_called_once_with([chunk.semantics])

        client.upsert.assert_called_once()
        point = client.upsert.call_args.kwargs["points"][0]

        assert point.vector[setting.vectors_name] == [1, 2, 3]
        assert point.id == chunk.get_point_id()

        expected_payload = {
            "id": "123",
            "name": "Test",
            "source": "tasty-note",
            "quantity": "1",
            "ingredients": ["a", "b"],
            "category": "tw",
            "tags": ["jp"],
            "chunk_type": "title",
        }
        assert point.payload == expected_payload


@pytest.mark.asyncio
async def test_qdr_repository_upsert_main_chunk_without_ingredients(recipe_without_ingredients):
    client = AsyncMock()
    embed_client = MagicMock()
    embed_client.post = AsyncMock()

    setting = RecipeQdrantSetting()

    repository = QdrantRepository(setting, client, embed_client)

    chunk = MainChunk.from_recipe(recipe_without_ingredients)

    with patch.object(repository, "_compute_embeddings", new_callable=AsyncMock) as mock_computer_embeddings:
        mock_computer_embeddings.return_value = [[1, 2, 3]]
        await repository.upsert_recipe(chunk)

        mock_computer_embeddings.assert_called_once_with([chunk.semantics])

        client.upsert.assert_called_once()
        point = client.upsert.call_args.kwargs["points"][0]

        assert point.vector[setting.vectors_name] == [1, 2, 3]
        assert point.id == chunk.get_point_id()

        expected_payload = {
            "id": "123",
            "name": "Test",
            "source": "tasty-note",
            "category": "tw",
            "tags": ["jp"],
            "chunk_type": "title",
        }
        assert point.payload == expected_payload


@pytest.mark.asyncio
async def test_qdr_repository_upsert_overview_chunk(recipe):
    client = AsyncMock()
    embed_client = MagicMock()
    embed_client.post = AsyncMock()

    setting = RecipeQdrantSetting()

    repository = QdrantRepository(setting, client, embed_client)

    chunk = OverviewChunk.from_recipe(recipe)

    with patch.object(repository, "_compute_embeddings", new_callable=AsyncMock) as mock_computer_embeddings:
        mock_computer_embeddings.return_value = [[1, 2, 3]]
        await repository.upsert_recipe(chunk)

        mock_computer_embeddings.assert_called_once_with([chunk.content])

        client.upsert.assert_called_once()
        point = client.upsert.call_args.kwargs["points"][0]

        assert point.vector[setting.vectors_name] == [1, 2, 3]
        assert point.id == chunk.get_point_id()

        expected_payload = {
            "id": "123",
            "source": "tasty-note",
            "chunk_type": "overview",
            "content": "Test"
        }
        assert point.payload == expected_payload


@pytest.mark.asyncio
async def test_qdr_repository_upsert_instruction_chunk(recipe):
    client = AsyncMock()
    embed_client = MagicMock()
    embed_client.post = AsyncMock()

    setting = RecipeQdrantSetting()

    repository = QdrantRepository(setting, client, embed_client)

    chunk = InstructionChunk.from_recipe(recipe)

    with patch.object(repository, "_compute_embeddings", new_callable=AsyncMock) as mock_computer_embeddings:
        mock_computer_embeddings.return_value = [[1, 2, 3]]
        await repository.upsert_recipe(chunk)

        mock_computer_embeddings.assert_called_once_with([chunk.content])

        client.upsert.assert_called_once()
        point = client.upsert.call_args.kwargs["points"][0]

        assert point.vector[setting.vectors_name] == [1, 2, 3]
        assert point.id == chunk.get_point_id()

        expected_payload = {
            "id": "123",
            "source": "tasty-note",
            "chunk_type": "instruction",
            "content": "ab"
        }
        assert point.payload == expected_payload


@pytest.mark.asyncio
async def test_qdr_repository_upsert_batch_chunk(recipe):
    client = AsyncMock()
    embed_client = MagicMock()
    embed_client.post = AsyncMock()

    setting = RecipeQdrantSetting()

    repository = QdrantRepository(setting, client, embed_client)

    chunks = [
        MainChunk.from_recipe(recipe),
        OverviewChunk.from_recipe(recipe),
        InstructionChunk.from_recipe(recipe)
    ]

    with patch.object(repository, "_compute_embeddings", new_callable=AsyncMock) as mock_computer_embeddings:
        mock_computer_embeddings.return_value = [[1], [2], [3]]
        await repository.upsert_batch_chunk(chunks)

        mock_computer_embeddings.assert_called_once()
        client.upsert.assert_called_once()
        points = client.upsert.call_args.kwargs["points"]
        assert len(points) == 3


@pytest.mark.asyncio
async def test_qdr_repository_upsert_batch_chunk(recipe_without_ingredients):
    client = AsyncMock()
    embed_client = MagicMock()
    embed_client.post = AsyncMock()

    setting = RecipeQdrantSetting()

    repository = QdrantRepository(setting, client, embed_client)

    chunks = [
        MainChunk.from_recipe(recipe_without_ingredients),
        OverviewChunk.from_recipe(recipe_without_ingredients),
        InstructionChunk.from_recipe(recipe_without_ingredients)
    ]

    with patch.object(repository, "_compute_embeddings", new_callable=AsyncMock) as mock_computer_embeddings:
        mock_computer_embeddings.return_value = [[1], [2], [3]]
        await repository.upsert_batch_chunk(chunks)

        mock_computer_embeddings.assert_called_once()
        client.upsert.assert_called_once()
        points = client.upsert.call_args.kwargs["points"]
        assert len(points) == 3

        collection_name = client.upsert.call_args.kwargs["collection_name"]
        assert collection_name == setting.collection_name

        expected_payload = {
            "id": "123",
            "source": "tasty-note",
            "chunk_type": "instruction",
            "content": "ab"
        }
        assert expected_payload in [p.payload for p in points]


@pytest.mark.asyncio
async def test_find_all_points_single_page():
    client = AsyncMock()
    embed_client = MagicMock()
    embed_client.post = AsyncMock()

    setting = RecipeQdrantSetting()

    repository = QdrantRepository(setting, client, embed_client)

    """測試情境 1：資料量少，一頁就拉完 (next_offset 為 None)"""
    # 1. 準備 Mock 資料
    mock_response = [MagicMock(), MagicMock()]

    # 模擬 scroll 回傳 (points, next_offset)
    client.scroll.return_value = (mock_response, None)

    # 2. 呼叫目標函式（手動將 mock_service 當成 self 傳入，或直接呼叫物件方法）
    result = await repository.find_all_points(batch_size=2)

    # 3. 驗證結果
    assert len(result) == 2
    assert result == mock_response

    # 驗證 client.scroll 只被呼叫了一次，且參數正確
    client.scroll.assert_called_once_with(
        collection_name=setting.collection_name,
        limit=2,
        offset=None,
        with_payload=True,
        with_vectors=True,
    )


@pytest.mark.asyncio
async def test_find_all_points_multiple_pages():
    client = AsyncMock()
    embed_client = MagicMock()
    embed_client.post = AsyncMock()

    setting = RecipeQdrantSetting()

    repository = QdrantRepository(setting, client, embed_client)

    """測試情境 2：資料量大，需要分頁讀取 (有多個 offset)"""
    # 1. 準備兩頁的 Mock 資料
    page1_records = [MagicMock()]
    page2_records = [MagicMock()]

    # 使用 side_effect 來讓連續呼叫回傳不同的值
    client.scroll.side_effect = [
        (page1_records, "offset_token_1"),  # 第一次呼叫，給下一個 offset
        (page2_records, None)  # 第二次呼叫，結束
    ]

    # 2. 呼叫目標函式
    result = await repository.find_all_points(batch_size=1)

    # 3. 驗證結果
    assert len(result) == 2
    assert result == page1_records + page2_records

    # 驗證 scroll 被呼叫了兩次
    assert client.scroll.call_count == 2

    # 驗證第二次呼叫時，確實有帶入前一次的 offset
    client.scroll.assert_called_with(
        collection_name=setting.collection_name,
        limit=1,
        offset="offset_token_1",
        with_payload=True,
        with_vectors=True,
    )


@pytest.mark.asyncio
async def test_find_all_points_empty():
    client = AsyncMock()
    embed_client = MagicMock()
    embed_client.post = AsyncMock()

    setting = RecipeQdrantSetting()

    repository = QdrantRepository(setting, client, embed_client)

    """測試情境 3：Collection 裡面完全沒有資料"""
    client.scroll.return_value = ([], None)

    result = await repository.find_all_points()

    assert result == []
    client.scroll.assert_called_once()
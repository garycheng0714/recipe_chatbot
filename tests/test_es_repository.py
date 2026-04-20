import pytest
import pytest_asyncio
from elasticsearch import AsyncElasticsearch

from app.infrastructure.elasticsearch.config import get_index_name, get_body_config, AnalyzerMode
from app.domain.models import EsPointsModel
from app.repositories import ElasticSearchRepository
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe, Ingredient, Step


@pytest_asyncio.fixture(scope="session")
async def es_client(es_container):
    """
    用 get_container_host_ip() + get_exposed_port(9200) 才能拿到正確的隨機 port：
    host = es_container.get_container_host_ip()  # 通常是 localhost
    port = es_container.get_exposed_port(9200)   # 例如 32847
    """
    host = es_container.get_container_host_ip()
    port = es_container.get_exposed_port(9200)

    client = AsyncElasticsearch(
        hosts=[f"http://{host}:{port}"],
        verify_certs=False,  # testcontainer 通常不需要 cert
    )
    yield client
    await client.close()


@pytest_asyncio.fixture(scope="session")
async def es_repo(es_client):
    """建立 index，回傳 repo，session 結束後刪掉 index"""
    # 建立 index（含 mapping）
    index_name = get_index_name()

    if not await es_client.indices.exists(index=index_name):
        await es_client.indices.create(
            index=index_name,
            body=get_body_config(AnalyzerMode.STANDARD)
        )
    repo = ElasticSearchRepository(es_client)
    yield repo
    await es_client.indices.delete(index=index_name, ignore_unavailable=True)


@pytest_asyncio.fixture(autouse=True)
async def cleanup_docs(es_client):
    """每個 test 結束後清空文件，避免測試間互相污染"""
    yield
    await es_client.delete_by_query(
        index=get_index_name(),
        body={"query": {"match_all": {}}},
        refresh=True,
    )


@pytest.fixture
def recipe():
    return TastyNoteRecipe(
        id="123",
        name="banana",
        source_url="https://example.com",
        category="jp",
        description="Good fruit",
        quantity="1",
        ingredients=[Ingredient(name="banana", amount="1")],
        steps=[Step(img="jpg", step="搗碎")],
        tags=["jp", "fruit"],
    )

@pytest.fixture
def index_name():
    return get_index_name()


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_indexes_parent_and_children(recipe, es_repo, es_client, index_name):
    await es_repo.index_recipe(recipe)

    # refresh 讓文件立刻可被搜尋
    await es_client.indices.refresh(index=index_name)

    result = await es_client.count(index=index_name)
    assert result["count"] == 3  # 至少 parent chunk 存進去了


async def test_search_name_in_parent_chunk(recipe, es_repo, es_client, index_name):
    await es_repo.index_recipe(recipe)

    # refresh 讓文件立刻可被搜尋
    await es_client.indices.refresh(index=index_name)

    result = await es_repo.search("banana")
    hits = EsPointsModel(**result).hits.hits

    assert len(hits) == 1
    assert hits[0].field_source.name == "banana"


async def test_search_keyword_in_parent_and_child_chunk(recipe, es_repo, es_client, index_name):
    await es_repo.index_recipe(recipe)

    # refresh 讓文件立刻可被搜尋
    await es_client.indices.refresh(index=index_name)

    result = await es_repo.search("fruit")
    hits = EsPointsModel(**result).hits.hits
    assert len(hits) == 2


async def test_search_description(recipe, es_repo, es_client, index_name):
    await es_repo.index_recipe(recipe)
    await es_client.indices.refresh(index=index_name)

    result = await es_repo.search("Good fruit")
    hits = EsPointsModel(**result).hits.hits

    assert len(hits) == 1

    data = hits[0].field_source
    assert data.content == recipe.description
    assert data.parent_id == recipe.id
    assert data.id == f"{recipe.id}_overview"


async def test_search_instruction(recipe, es_repo, es_client, index_name):
    await es_repo.index_recipe(recipe)
    await es_client.indices.refresh(index=index_name)

    result = await es_repo.search("搗碎")
    hits = EsPointsModel(**result).hits.hits

    assert len(hits) == 1

    data = hits[0].field_source
    assert data.content == "搗碎"
    assert data.parent_id == recipe.id
    assert data.id == f"{recipe.id}_instruction"


async def test_name_field_boosted_over_content(es_repo, es_client, index_name):
    await es_repo.index_recipe(TastyNoteRecipe(id="r1", name="咖哩飯", description="普通料理", source_url="url", quantity="1", category="a", tags=[], ingredients=[],steps=[]))
    await es_repo.index_recipe(TastyNoteRecipe(id="r2", name="普通料理", description="含有咖哩粉", source_url="url2", quantity="1", category="b", tags=[], ingredients=[], steps=[]))
    await es_client.indices.refresh(index=index_name)

    result = await es_repo.search("咖哩")
    hits = EsPointsModel(**result).hits.hits

    assert len(hits) == 2
    assert hits[0].field_source.id == "r1"


async def test_search_no_results(recipe, es_repo, es_client, index_name):
    await es_repo.index_recipe(recipe)
    await es_client.indices.refresh(index=index_name)

    result = await es_repo.search("apple")
    hits = EsPointsModel(**result).hits.hits

    assert len(hits) == 0
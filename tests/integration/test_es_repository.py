import pytest
import pytest_asyncio
from elasticsearch import AsyncElasticsearch
from testcontainers.elasticsearch import ElasticSearchContainer

from app.domain.document import RecipeDocument
from app.infrastructure.elasticsearch.config.recipe_for_test import RecipeTestConfig
from app.repositories import ElasticSearchRepository

from app.domain.models import EsPointsModel
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe, Ingredient, Step


@pytest.fixture(scope="session")
def es_container():
    with ElasticSearchContainer("elasticsearch:9.1.4") as es:
        yield es


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
    index_name = RecipeTestConfig.index_name()

    if not await es_client.indices.exists(index=index_name):
        await es_client.indices.create(
            index=index_name,
            body=RecipeTestConfig.get_index_config()
        )
    repo = ElasticSearchRepository(es_client)
    yield repo
    await es_client.indices.delete(index=index_name, ignore_unavailable=True)


@pytest_asyncio.fixture(autouse=True)
async def cleanup_docs(es_client):
    """每個 test 結束後清空文件，避免測試間互相污染"""
    yield
    await es_client.delete_by_query(
        index=RecipeTestConfig.index_name(),
        body={"query": {"match_all": {}}},
        conflicts="proceed",
        refresh=True,
    )


@pytest.fixture
def recipe():
    return TastyNoteRecipe(
        id="123",
        name="banana",
        source_url="https://example.com",
        category="tw",
        description="Good fruit",
        quantity="1",
        ingredients=[Ingredient(name="a", amount="1"), Ingredient(name="b", amount="1")],
        steps=[Step(img="jpg", step="搗碎")],
        tags=["jp"],
    )


@pytest.fixture
def index_name():
    return RecipeTestConfig.index_name()


pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest_asyncio.fixture
async def setup(es_repo, es_client, recipe, index_name):
    document = RecipeDocument.from_recipe(recipe)

    await es_repo.index_document(index_name, document)

    # refresh 讓文件立刻可被搜尋
    await es_client.indices.refresh(index=index_name)


@pytest_asyncio.fixture
async def bulk_setup(es_client, es_repo, index_name, recipe):
    document = RecipeDocument.from_recipe(recipe)

    await es_repo.index_batch_document(index_name, [document])
    await es_client.indices.refresh(index=index_name)


async def test_indexes_parent_and_children(setup, recipe, es_repo, es_client, index_name):
    result = await es_client.count(index=index_name)
    assert result["count"] == 1  # 至少 parent chunk 存進去了


async def test_search_name_in_parent_chunk(setup, recipe, es_repo, es_client, index_name):
    result = await es_repo.search(index_name, "banana")
    hits = EsPointsModel(**result).hits.hits

    assert len(hits) == 1
    assert hits[0].field_source.name == "banana"


async def test_index_twice_then_search_one_result(setup, recipe, es_repo, es_client, index_name):
    document = RecipeDocument.from_recipe(recipe)

    await es_repo.index_document(index_name, document)
    await es_client.indices.refresh(index=index_name)

    result = await es_repo.search(index_name, "banana")
    hits = EsPointsModel(**result).hits.hits
    assert len(hits) == 1


async def test_search_keyword_in_parent_and_child_chunk(setup, recipe, es_repo, es_client, index_name):
    result = await es_repo.search(index_name, "jp")
    hits = EsPointsModel(**result).hits.hits
    assert len(hits) == 1


async def test_search_description(setup, recipe, es_repo, es_client, index_name):
    result = await es_repo.search(index_name, "Good fruit")
    hits = EsPointsModel(**result).hits.hits

    assert len(hits) == 1

    data = hits[0].field_source
    assert data.description == recipe.description
    assert data.id == f"{recipe.id}"


async def test_search_instruction(setup, recipe, es_repo, es_client, index_name):
    result = await es_repo.search(index_name, "搗碎")
    hits = EsPointsModel(**result).hits.hits

    assert len(hits) == 1

    data = hits[0].field_source
    assert data.steps == "搗碎"
    assert data.id == f"{recipe.id}"


# async def test_name_field_boosted_over_content(es_repo, es_client, index_name):
#     await es_repo.index_recipe(TastyNoteRecipe(id="r1", name="咖哩飯", description="普通料理", source_url="url", quantity="1", category="a", tags=[], ingredients=[],steps=[]))
#     await es_repo.index_recipe(TastyNoteRecipe(id="r2", name="普通料理", description="含有咖哩粉", source_url="url2", quantity="1", category="b", tags=[], ingredients=[], steps=[]))
#     await es_client.indices.refresh(index=index_name)
#
#     result = await es_repo.search("咖哩")
#     hits = EsPointsModel(**result).hits.hits
#
#     assert len(hits) == 2
#     assert hits[0].field_source.id == "r1"


async def test_search_no_results(setup, recipe, es_repo, es_client, index_name):
    result = await es_repo.search(index_name, "apple")
    hits = EsPointsModel(**result).hits.hits

    assert len(hits) == 0


async def test_index_bulk_chunk(bulk_setup, recipe, es_client, index_name):
    result = await es_client.count(index=index_name)
    assert result["count"] == 1


async def test_the_idempotence_of_index_bulk_chunk(bulk_setup, recipe, es_client, es_repo, index_name):
    document = RecipeDocument.from_recipe(recipe)

    await es_repo.index_batch_document(index_name, [document])
    await es_client.indices.refresh(index=index_name)

    result = await es_client.count(index=index_name)
    assert result["count"] == 1
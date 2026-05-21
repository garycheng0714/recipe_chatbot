import asyncio
from unittest.mock import MagicMock, AsyncMock

import httpx
import pytest

from app.dependencies.url_consumer_deps import UrlConsumerDeps
from app.utils.queue_iterator import STOP_SIGNAL
from web_crawler.consumer.url_consumer import UrlConsumer
from web_crawler.exceptions import RequestFatalError, RequestBlockedError, RequestRetryableError, ContentParsingError
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe


@pytest.fixture
def queue():
    return asyncio.Queue()


@pytest.fixture
def deps():
    return UrlConsumerDeps(
        crawler=MagicMock(),
        requester=MagicMock(),
        result_queue=asyncio.Queue(),
        limiter=MagicMock()
    )

@pytest.fixture
def recipe():
    return TastyNoteRecipe(
        id="1",
        name="123",
        source_url="https://example.com"
    )

@pytest.mark.asyncio
async def test_consumer_stop_when_no_task_in_queue(queue, deps, recipe):
    await queue.put(recipe.source_url)
    await queue.put(STOP_SIGNAL)

    consumer = UrlConsumer(
        url_queue=queue,
        deps=deps
    )

    consumer._get_recipe = AsyncMock(side_effect=[recipe])

    await consumer.run()

    # join() 應該立刻結束，不會卡住
    await asyncio.wait_for(queue.join(), timeout=1.0)

    assert deps.result_queue.qsize() == 1

    result = await deps.result_queue.get()
    assert result.source_url == recipe.source_url
    assert result.status == "completed"
    assert result.data == recipe


@pytest.mark.asyncio
async def test_consumer_handle_multiple_results(queue, deps, recipe):
    await queue.put("https://example.com")
    await queue.put("https://example2.com")
    await queue.put(STOP_SIGNAL)

    consumer = UrlConsumer(
        url_queue=queue,
        deps=deps
    )

    consumer._get_recipe = AsyncMock(side_effect=[
        recipe,
        RequestFatalError("error")
    ])

    await consumer.run()

    await asyncio.wait_for(queue.join(), timeout=1.0)
    assert deps.result_queue.qsize() == 2

    result = [await deps.result_queue.get() for _ in range(2)]
    statuses = {r.source_url: r.status for r in result}
    assert statuses["https://example.com"] == "completed"
    assert statuses["https://example2.com"] == "failed"


@pytest.mark.asyncio
@pytest.mark.parametrize("exception, status",[
    (RequestFatalError("Fatal Error"), "failed"),
    (RequestBlockedError("Blocked"), "retry"),
    (RequestRetryableError("Retryable Network Error"), "retry"),
    (ContentParsingError("Parsing Error"), "parsing_error"),
    (httpx.ConnectTimeout("Unknown Error", request=MagicMock()), "failed"),
])
async def test_consumer_raises_fatal_exception(queue, deps, recipe, exception, status):
    await queue.put(recipe.source_url)
    await queue.put(STOP_SIGNAL)

    consumer = UrlConsumer(
        url_queue=queue,
        deps=deps
    )

    consumer._get_recipe = AsyncMock(side_effect=[
        exception
    ])

    await consumer.run()

    # join() 應該立刻結束，不會卡住
    await asyncio.wait_for(queue.join(), timeout=1.0)

    assert deps.result_queue.qsize() == 1

    result = await deps.result_queue.get()
    assert result.source_url == recipe.source_url
    assert result.status == status
    assert result.data is None
    assert result.error_msg == str(exception)
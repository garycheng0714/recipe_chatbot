import asyncio
from unittest.mock import AsyncMock

import pytest

from web_crawler.service.crawler_app import CrawlerApp


@pytest.fixture
def read_mock_data():

    def _read(filename: str) -> str:
        with open("web_crawler/tests/mocks/{}".format(filename), "r") as f:
            html = f.read()
        return html

    return _read

"""
For crawler app
"""

@pytest.fixture
def stop_event():
    return asyncio.Event()

@pytest.fixture
def url_queue():
    return asyncio.Queue()

@pytest.fixture
def result_queue():
    return asyncio.Queue()

@pytest.fixture
def mock_producer():
    producer = AsyncMock()
    producer.run = AsyncMock(return_value=None)
    return producer

@pytest.fixture
def mock_storage_worker(stop_event, result_queue):
    worker = AsyncMock()
    worker.run = AsyncMock(side_effect=asyncio.CancelledError)
    return worker

@pytest.fixture
def mock_stale_worker(stop_event):
    worker = AsyncMock()
    worker.run = AsyncMock(side_effect=asyncio.CancelledError)
    return worker

@pytest.fixture
def mock_consumer_factory(url_queue):
    def factory():
        consumer = AsyncMock()
        consumer.run = AsyncMock(side_effect=asyncio.CancelledError)
        return consumer
    return factory

@pytest.fixture
def mock_app(url_queue, result_queue, mock_consumer_factory, mock_stale_worker, mock_producer, mock_storage_worker, stop_event):
    return CrawlerApp(
        stop_event=stop_event,
        producer=mock_producer,
        stale_event_worker=mock_stale_worker,
        storage_worker=mock_storage_worker,
        consumer_factory=mock_consumer_factory,
        url_queue=url_queue,
        result_queue=result_queue,
        max_workers=5
    )
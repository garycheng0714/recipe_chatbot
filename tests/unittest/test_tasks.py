from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from tasks.tasks import sync_to_distributed_db

@pytest.fixture(autouse=True)
def speed_up_tenacity():
    """自動將 asyncio.sleep 設為 AsyncMock，讓等待瞬間完成"""
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        yield mock_sleep


@pytest.fixture
def mock_session_factory():
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.begin = MagicMock(return_value=mock_session)

    factory = MagicMock(return_value=mock_session)
    return factory


@pytest.mark.asyncio
async def test_no_pending_events_will_stop_tasks(mock_session_factory):
    es = MagicMock()
    qdr = MagicMock()
    outbox = MagicMock()
    outbox.claim_event = AsyncMock(return_value=None)
    outbox.mark_event_completed = AsyncMock()

    await sync_to_distributed_db(
        MagicMock(),
        es,
        qdr,
        outbox,
        mock_session_factory
    )

    outbox.claim_event.assert_called_once()
    outbox.mark_event_completed.assert_not_called()


@pytest.mark.asyncio
async def test_mark_event_completed(mock_session_factory):
    payload = MagicMock()

    es = MagicMock()
    es.index_batch_chunk = AsyncMock()

    qdr = MagicMock()
    qdr.upsert_batch_recipe = AsyncMock()

    outbox = MagicMock()
    outbox.claim_event = AsyncMock()
    outbox.mark_event_completed = AsyncMock()

    await sync_to_distributed_db(
        payload,
        es,
        qdr,
        outbox,
        mock_session_factory
    )

    outbox.claim_event.assert_called_once()
    outbox.mark_event_completed.assert_called_once()

    assert es.index_batch_chunk.call_count == 1
    assert qdr.upsert_batch_recipe.call_count == 1


@pytest.mark.asyncio
async def test_qdr_upsert_fail_will_mark_event_failed(mock_session_factory):
    payload = MagicMock()

    es = MagicMock()
    es.index_batch_chunk = AsyncMock()

    qdr = MagicMock()
    qdr.upsert_batch_recipe = AsyncMock(side_effect=Exception("boom"))

    outbox = MagicMock()
    outbox.claim_event = AsyncMock()
    outbox.mark_event_completed = AsyncMock()
    outbox.mark_event_failed = AsyncMock()

    # context = MagicMock()
    # context.message.labels.get = MagicMock(return_value=2)

    with pytest.raises(Exception):
        await sync_to_distributed_db(
            payload,
            es,
            qdr,
            outbox,
            mock_session_factory
        )

    outbox.claim_event.assert_called_once()
    outbox.mark_event_completed.assert_not_called()
    outbox.mark_event_failed.assert_called_once()


@pytest.mark.asyncio
async def test_es_index_fail_will_mark_event_failed(mock_session_factory):
    payload = MagicMock()

    es = MagicMock()
    es.index_batch_chunk = AsyncMock(side_effect=Exception("boom"))

    qdr = MagicMock()
    qdr.upsert_batch_recipe = AsyncMock()

    outbox = MagicMock()
    outbox.claim_event = AsyncMock()
    outbox.mark_event_completed = AsyncMock()
    outbox.mark_event_failed = AsyncMock()

    # context = MagicMock()
    # context.message.labels.get = MagicMock(return_value=2)

    with pytest.raises(Exception):
        await sync_to_distributed_db(
            payload,
            es,
            qdr,
            outbox,
            mock_session_factory
        )

    outbox.claim_event.assert_called_once()
    outbox.mark_event_completed.assert_not_called()
    outbox.mark_event_failed.assert_called_once()


# @pytest.mark.asyncio
# @pytest.mark.parametrize("retry_label", [0, 1])
# async def test_sync_fail_first_time_will_not_mark_event_fail(retry_label, mock_session_factory):
#     payload = MagicMock()
#
#     es = MagicMock()
#     es.index_batch_chunk = AsyncMock()
#
#     qdr = MagicMock()
#     qdr.upsert_batch_recipe = AsyncMock(side_effect=Exception("boom"))
#
#     outbox = MagicMock()
#     outbox.claim_event = AsyncMock()
#     outbox.mark_event_completed = AsyncMock()
#     outbox.mark_event_failed = AsyncMock()
#
#     context = MagicMock()
#     context.message.labels.get = MagicMock(return_value=retry_label)
#
#     with pytest.raises(Exception):
#         await sync_to_distributed_db(
#             payload,
#             es,
#             qdr,
#             outbox,
#             context,
#             mock_session_factory
#         )
#
#     outbox.claim_event.assert_called_once()
#     outbox.mark_event_completed.assert_not_called()
#     outbox.mark_event_failed.assert_not_called()



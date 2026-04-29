from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tasks.outbox_poller import poll_outbox

@pytest.fixture
def patch_transformers():
    with patch("tasks.outbox_poller.TastyNoteRecipe"), \
         patch("tasks.outbox_poller.MainChunk"), \
         patch("tasks.outbox_poller.OverviewChunk"), \
         patch("tasks.outbox_poller.InstructionChunk"), \
         patch("tasks.outbox_poller.DistributedPayload"):
        yield


@pytest.mark.asyncio
async def test_outbox_poller_no_pending_event(patch_transformers):
    outbox_repo = MagicMock()
    outbox_repo.reset_stale_events = AsyncMock()
    outbox_repo.get_pending_events = AsyncMock(return_value=[])

    dispatch_fn = AsyncMock()

    await poll_outbox(outbox_repo, dispatch_fn)

    outbox_repo.reset_stale_events.assert_called_once()
    outbox_repo.get_pending_events.assert_called_once()
    dispatch_fn.assert_not_called()


@pytest.mark.asyncio
async def test_outbox_poller_handle_one_pending_event(patch_transformers):
    outbox_repo = MagicMock()
    outbox_repo.reset_stale_events = AsyncMock()
    outbox_repo.get_pending_events = AsyncMock(return_value=[MagicMock()])

    dispatch_fn = AsyncMock()

    await poll_outbox(outbox_repo, dispatch_fn)

    outbox_repo.reset_stale_events.assert_called_once()
    outbox_repo.get_pending_events.assert_called_once()
    dispatch_fn.assert_called_once()


@pytest.mark.asyncio
async def test_outbox_poller_handle_multiple_pending_event(patch_transformers):
    outbox_repo = MagicMock()
    outbox_repo.reset_stale_events = AsyncMock()
    outbox_repo.get_pending_events = AsyncMock(return_value=[MagicMock(), MagicMock(), MagicMock()])

    dispatch_fn = AsyncMock()

    await poll_outbox(outbox_repo, dispatch_fn)

    outbox_repo.reset_stale_events.assert_called_once()
    outbox_repo.get_pending_events.assert_called_once()
    assert dispatch_fn.call_count == 3


@pytest.mark.asyncio
async def test_outbox_poller_reset_stale_event_fail(patch_transformers):
    outbox_repo = MagicMock()
    outbox_repo.reset_stale_events = AsyncMock(side_effect=Exception("DB Error!"))
    outbox_repo.get_pending_events = AsyncMock(return_value=[])

    dispatch_fn = AsyncMock()

    with pytest.raises(Exception):
        await poll_outbox(outbox_repo, dispatch_fn)

    outbox_repo.get_pending_events.assert_not_called()
    dispatch_fn.assert_not_called()


@pytest.mark.asyncio
async def test_outbox_poller_get_pending_events_fail(patch_transformers):
    outbox_repo = MagicMock()
    outbox_repo.reset_stale_events = AsyncMock()
    outbox_repo.get_pending_events = AsyncMock(side_effect=Exception("DB Error!"))

    dispatch_fn = AsyncMock()

    with pytest.raises(Exception):
        await poll_outbox(outbox_repo, dispatch_fn)

    outbox_repo.reset_stale_events.assert_called_once()
    dispatch_fn.assert_not_called()
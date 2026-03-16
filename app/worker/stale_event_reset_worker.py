import asyncio
from datetime import timedelta, UTC, datetime

from app.database import AsyncSessionLocal
from app.repositories import PgRepository


class StaleEventResetWorker:
    def __init__(
        self,
        pg_repo: PgRepository,
        stop_event: asyncio.Event,
        session_factory=None,
        interval_minutes: float = 30.0
    ):
        self.pg_repo = pg_repo
        self.stop_event = stop_event
        self.session_factory = session_factory or AsyncSessionLocal
        self.interval_minutes = interval_minutes

    async def run(self):
        while not self.stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self.stop_event.wait(),
                    timeout=self.interval_minutes * 60   # 等待 stop 或 interval 到期
                )
            except asyncio.TimeoutError:
                # timeout 到了，繼續下一次 reset
                cut_off = datetime.now(UTC) - timedelta(minutes=self.interval_minutes)
                await self._reset_stale_events(cut_off)

    async def _reset_stale_events(self, cut_off: datetime):
        async with self.session_factory() as session:
            async with session.begin():
                await self.pg_repo.reset_stale_events(session, cut_off)
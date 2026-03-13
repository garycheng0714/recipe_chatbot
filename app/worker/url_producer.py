import asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.database import AsyncSessionLocal
from app.repositories import PgRepository
from loguru import logger
import sqlalchemy.exc


# 定義重試規則：如果是資料庫連線相關錯誤，自動重試
# wait_exponential 會讓重試間隔變成 1s, 2s, 4s, 8s... 避免打死剛重啟的 DB
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((
        sqlalchemy.exc.OperationalError,
        sqlalchemy.exc.DisconnectionError,
    )),
    reraise=True
)
async def _fetch_batch_with_retry(session_factory: async_sessionmaker, pg_repo: PgRepository):
    async with session_factory() as session:
        async with session.begin():
            return await pg_repo.get_next_url_batch(session, batch_size=50)


class UrlProducer:
    def __init__(
        self,
        pg_repo: PgRepository,
        url_queue: asyncio.Queue,
        stop_event: asyncio.Event,
        session_factory=None
    ):
        self.pg_repo = pg_repo
        self.url_queue = url_queue
        self.stop_event = stop_event
        self.session_factory = session_factory or AsyncSessionLocal

    async def run(self):
        await self.reset_stale_events()

        loop = asyncio.get_running_loop()
        reset_time = loop.time() + 30 * 60

        while not self.stop_event.is_set():
            if loop.time() >= reset_time:
                reset_time = loop.time() + 30 * 60
                await self.reset_stale_events()

            try:
                # 1. 從 DB 撈一批 (例如 50 筆)
                batch = await _fetch_batch_with_retry(self.session_factory, self.pg_repo)

                # 2. 如果沒資料了，代表全爬完，跳出循環
                if not batch:
                    print("🏁 所有 pending URL 已處理完畢")
                    break

                # 3. 塞進 Queue 讓 Consumer 消化
                for url in batch:
                    # put 的時候也要檢查 shutdown，避免卡住
                    if self.stop_event.is_set():
                        print("Stop event!!!!")
                        break
                    await self.url_queue.put(url)
                    print(f"Added {url} to queue")

                # 撈完一批後看 queue 狀況
                print(f"queue size: {self.url_queue.qsize()}/{self.url_queue.maxsize}")
            except Exception as e:
                # 這裡捕獲所有重試失敗後或是非預期的錯誤
                logger.exception(e)
                raise

            await self._sleep()

    async def reset_stale_events(self):
        async with self.session_factory() as session:
            async with session.begin():
                await self.pg_repo.reset_stale_events(session)

    async def _sleep(self):
        await asyncio.sleep(1)
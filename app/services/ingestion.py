from typing import List

from sqlalchemy.ext.asyncio.session import AsyncSession
from app.repositories import PgRepository
from app.repositories.outbox_repository import OutboxRepository
from app.services.converter import PgConverter
from app.services.event.recipe_event import RecipeEvent
from web_crawler.schema.crawl_result_schema import CrawlResult
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe


class IngestionService:
    def __init__(self, pg_repo: PgRepository, outbox_repo: OutboxRepository):
        self.pg_repo = pg_repo
        self.outbox_repo = outbox_repo

    async def ingest_crawl_completed_data(self, session: AsyncSession, crawl_result: CrawlResult):
        recipe = crawl_result.data

        chunk = PgConverter.to_main_chunk(recipe)
        await self.pg_repo.update_recipe(session, chunk)

        chunks = [
            PgConverter.to_overview_chunk(recipe),
            PgConverter.to_instruction_chunk(recipe)
        ]
        await self.pg_repo.add_recipe_chunk(session, chunks)

        outbox_event = RecipeEvent.create(recipe)

        await self.outbox_repo.insert_event(session, outbox_event)

    async def ingest_crawl_bulk_data(self, session: AsyncSession, crawl_results: List[CrawlResult]):
        recipes = [r.data for r in crawl_results]

        models = [
            PgConverter.to_main_chunk(recipe)
            for recipe in recipes
        ]
        await self.pg_repo.update_bulk_recipe(session, models)

        child_models = []
        for recipe in recipes:
            child_models.append(PgConverter.to_overview_chunk(recipe))
            child_models.append(PgConverter.to_instruction_chunk(recipe))

        await self.pg_repo.add_bulk_recipe_chunk(session, child_models)

        outbox_events = [RecipeEvent.create(recipe) for recipe in recipes]

        await self.outbox_repo.insert_bulk_event(session, outbox_events)

    async def ingest_pending_url(self, session: AsyncSession, recipe: TastyNoteRecipe):
        await self.pg_repo.insert_pending_url(session, recipe)

    async def update_crawl_status(self, session: AsyncSession, crawl_result: CrawlResult):
        await self.pg_repo.update_crawler_status(session, crawl_result)

    async def update_bulk_crawl_status(self, session: AsyncSession, crawl_results: List[CrawlResult]):
        await self.pg_repo.update_bulk_crawl_status(session, crawl_results)


def get_ingestion_service():
    return IngestionService(pg_repo=PgRepository(), outbox_repo=OutboxRepository())
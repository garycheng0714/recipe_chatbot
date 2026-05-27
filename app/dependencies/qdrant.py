from taskiq import Context, TaskiqDepends

from app.repositories.qdr_repository import QdrantRepository


async def get_qdrant(
    context: Context = TaskiqDepends(),
):
    yield QdrantRepository(
        context.state.qdr_client,
        context.state.embed_client,
    )
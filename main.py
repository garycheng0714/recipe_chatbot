from time import sleep
from urllib.parse import urlparse

from postgre_db import PostgreDB, RecipeModel, RecipeChunkModel
from recipe_entity import RecipeEntity
from scraper import scrape_recipe, fetch_recipes
from elastic_search import ElasticSearchHelper
from qdrant_db import QdrantVectorStore


if __name__ == "__main__":
    es = ElasticSearchHelper()
    qdrant = QdrantVectorStore()
    db = PostgreDB()

    recipes_url = fetch_recipes("https://tasty-note.com/tag/ten-minutes/")

    sleep(3)

    for url in recipes_url:
        sleep(2)
        print(f"Fetching {url}")
        data = scrape_recipe(url)
        id = urlparse(url).path.split("/")[1]

        recipe = RecipeEntity(id, data)

        parent_chunk = recipe.to_document()
        chunks = recipe.to_chunks()

        es.index_chunk(parent_chunk.to_dict())
        db.add_recipe(RecipeModel(**recipe.to_document().to_dict()))

        for chunk in chunks:
            qdrant.upsert(chunk)
            es.index_chunk(chunk.to_dict())
            db.add_chunk(RecipeChunkModel(**chunk.to_dict()))

    db.commit()
    db.close()



from pydantic import BaseModel, HttpUrl

from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe


class DetailUrl(BaseModel):
    id: str
    url: HttpUrl

    def to_recipe(self) -> TastyNoteRecipe:
        return TastyNoteRecipe(id=self.id, source_url=str(self.url))
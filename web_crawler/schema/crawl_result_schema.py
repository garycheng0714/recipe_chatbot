from typing import Literal, Optional
from pydantic import BaseModel
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe


class CrawlResult(BaseModel):
    source_url: str
    status: Literal["pending", "processing", "completed", "failed", "retry", "parsing_error"]
    data: Optional[TastyNoteRecipe] = None
    error_msg: Optional[str] = None
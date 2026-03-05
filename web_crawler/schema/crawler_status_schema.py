from typing import Literal, Optional
from pydantic import BaseModel


class CrawlerStatusUpdate(BaseModel):
    source_url: str
    status: Literal["pending", "processing", "completed", "failed", "retry", "parsing_error"]
    error_msg: Optional[str] = None
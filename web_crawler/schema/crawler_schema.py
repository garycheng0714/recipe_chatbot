from pydantic import BaseModel, HttpUrl, Field

class DetailUrl(BaseModel):
    url: HttpUrl
from pydantic import BaseModel, HttpUrl

class DetailUrl(BaseModel):
    id: str
    url: HttpUrl

    def get_url(self) -> str:
        return str(self.url)
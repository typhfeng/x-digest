from dataclasses import dataclass

@dataclass
class Post:
    id: str
    author: str
    text: str
    url: str | None = None
    created_at: str | None = None

from dataclasses import dataclass, field
from time import time


@dataclass
class User:
    id: str
    email: str
    name: str
    picture: str


@dataclass
class Session:
    id: str
    user: User
    created_at: float = field(default_factory=time)

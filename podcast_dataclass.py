from dataclasses import dataclass

# TODO: Maybe delete
@dataclass
class Podcast:
    author: str
    title: str
    entities: dict

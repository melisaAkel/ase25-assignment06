# dto.py
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class RoomDto:
    id: int
    type: str
    title: str
    description: str
    price_eur: int
    capacity: int
    available: bool
    booked_count: int
    remaining: int
    is_full: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "price_eur": self.price_eur,
            "capacity": self.capacity,
            "available": self.available,
            "booked_count": self.booked_count,
            "remaining": self.remaining,
            "is_full": self.is_full,
        }


@dataclass
class EventDto:
    id: int
    title: str
    category: str
    date_time: str
    location: str
    description: str
    quota: Optional[int]
    registered_count: int
    remaining: Optional[int]
    is_full: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "date_time": self.date_time,
            "location": self.location,
            "description": self.description,
            "quota": self.quota,
            "registered_count": self.registered_count,
            "remaining": self.remaining,
            "is_full": self.is_full,
        }


@dataclass
class InfoPageDto:
    id: int
    slug: str
    title: str
    content: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "slug": self.slug,
            "title": self.title,
            "content": self.content,
        }

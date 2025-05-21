# health_app/services/base_service.py
from typing import TypeVar, Generic, Optional
from uuid import UUID
from health_app.repositories.base_repository import BaseRepository

T = TypeVar('T')  # Generic type for schemas

class BaseService(Generic[T]):
    def __init__(self, repository: BaseRepository):
        self.repository = repository

    def get(self, entity_id: UUID) -> Optional[T]:
        return self.repository.get(entity_id)

    def list(self, page: int = 1, page_size: int = 10, **filters) -> list[T]:
        return self.repository.list(page=page, page_size=page_size, **filters)

    def create(self, data: dict) -> T:
        return self.repository.create(data)

    def update(self, entity_id: UUID, updates: dict) -> Optional[T]:
        return self.repository.update(entity_id, updates)

    def delete(self, entity_id: UUID) -> bool:
        return self.repository.delete(entity_id)
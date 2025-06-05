from typing import Any, Dict, List, Optional, TypeVar

from fastapi import Depends
from sqlalchemy import and_
from sqlalchemy.orm import Session, selectinload

from app.database.base import get_db
from app.models import (
    Association,
    Event,
    EventAssociation,
    EventVolunteer,
    User,
    Volunteer,
)
from app.models.event import EventStatus

T = TypeVar("T")


class DatabaseService:
    """Optimized database service with relationship loading and query optimization."""

    def __init__(self, db: Session):
        self.db = db

    # Association queries
    def get_associations_with_volunteers(
        self, skip: int = 0, limit: int = 100
    ) -> List[Association]:
        """Get associations with volunteers in a single optimized query."""
        return (
            self.db.query(Association)
            .options(selectinload(Association.volunteers))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_association_by_id(self, association_id: int) -> Optional[Association]:
        """Get association by ID with volunteers loaded."""
        return (
            self.db.query(Association)
            .options(selectinload(Association.volunteers))
            .filter(Association.id == association_id)
            .first()
        )

    def get_association_volunteers(self, association_id: int) -> List[Volunteer]:
        """Get volunteers for a specific association."""
        return (
            self.db.query(Volunteer)
            .filter(Volunteer.association_id == association_id)
            .all()
        )

    # Event queries optimized
    def get_events_with_associations(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[EventStatus] = None,
    ) -> List[Event]:
        """Get events with all associations and volunteers in optimized queries."""
        query = self.db.query(Event).options(
            selectinload(Event.event_associations)
            .selectinload(EventAssociation.volunteers)
            .selectinload(EventVolunteer.volunteer),
            selectinload(Event.event_associations).selectinload(
                EventAssociation.association
            ),
        )

        if status_filter:
            query = query.filter(Event.status == status_filter)

        return query.offset(skip).limit(limit).all()

    def get_event_by_id_with_details(self, event_id: int) -> Optional[Event]:
        """Get single event with all related data optimized."""
        return (
            self.db.query(Event)
            .options(
                selectinload(Event.event_associations)
                .selectinload(EventAssociation.volunteers)
                .selectinload(EventVolunteer.volunteer),
                selectinload(Event.event_associations).selectinload(
                    EventAssociation.association
                ),
            )
            .filter(Event.id == event_id)
            .first()
        )

    def get_event_association(
        self, event_id: int, association_id: int
    ) -> Optional[EventAssociation]:
        """Get specific event-association relationship."""
        return (
            self.db.query(EventAssociation)
            .filter(
                and_(
                    EventAssociation.event_id == event_id,
                    EventAssociation.association_id == association_id,
                )
            )
            .first()
        )

    # User queries
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()

    # Generic CRUD operations
    def create(self, obj: T) -> T:
        """Create a new object."""
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: T, update_data: Dict[str, Any]) -> T:
        """Update an object with new data."""
        for field, value in update_data.items():
            if hasattr(obj, field):
                setattr(obj, field, value)

        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: T) -> bool:
        """Delete an object."""
        try:
            self.db.delete(obj)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    def bulk_create(self, objects: List[T]) -> List[T]:
        """Create multiple objects efficiently."""
        self.db.add_all(objects)
        self.db.commit()
        for obj in objects:
            self.db.refresh(obj)
        return objects


# Dependency for getting database service
def get_database_service(db: Session = Depends(get_db)) -> DatabaseService:
    """Dependency to get database service instance."""
    return DatabaseService(db)

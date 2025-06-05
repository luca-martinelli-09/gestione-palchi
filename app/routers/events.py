from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.auth import get_current_active_user
from app.models.auth import User
from app.models.event import EventStatus
from app.schemas.event import (
    EventAssociationCreate,
    EventCreate,
    EventUpdate,
    EventWithCalculationsAndDetails,
)
from app.services.database import DatabaseService, get_database_service
from app.services.event_service import EventService

router = APIRouter()


def get_event_service(
    db_service: DatabaseService = Depends(get_database_service),
) -> EventService:
    """Dependency to get event service instance."""
    return EventService(db_service)


@router.post(
    "/",
    response_model=EventWithCalculationsAndDetails,
    status_code=status.HTTP_201_CREATED,
)
async def create_event(
    event: EventCreate,
    event_service: EventService = Depends(get_event_service),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new event."""
    return event_service.create_event(event)


@router.get("/", response_model=List[EventWithCalculationsAndDetails])
async def get_events(
    skip: int = 0,
    limit: int = Query(100, le=1000),  # Limit max to prevent overload
    status_filter: Optional[EventStatus] = Query(None, alias="status"),
    event_service: EventService = Depends(get_event_service),
    current_user: User = Depends(get_current_active_user),
):
    """Get events with pagination and optional status filter."""
    return event_service.get_events(skip=skip, limit=limit, status_filter=status_filter)


@router.get("/{event_id}", response_model=EventWithCalculationsAndDetails)
async def get_event(
    event_id: int,
    event_service: EventService = Depends(get_event_service),
    current_user: User = Depends(get_current_active_user),
):
    """Get single event with details."""
    return event_service.get_event_by_id(event_id)


@router.put("/{event_id}", response_model=EventWithCalculationsAndDetails)
async def update_event(
    event_id: int,
    event_update: EventUpdate,
    event_service: EventService = Depends(get_event_service),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing event."""
    return event_service.update_event(event_id, event_update)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    event_service: EventService = Depends(get_event_service),
    current_user: User = Depends(get_current_active_user),
):
    """Delete an event."""
    event_service.delete_event(event_id)


@router.post("/{event_id}/associations", status_code=status.HTTP_201_CREATED)
async def assign_association_to_event(
    event_id: int,
    association_data: EventAssociationCreate,
    event_service: EventService = Depends(get_event_service),
    current_user: User = Depends(get_current_active_user),
):
    """Assign an association to an event."""
    return event_service.assign_association_to_event(event_id, association_data)


@router.delete(
    "/{event_id}/associations/{association_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_association_from_event(
    event_id: int,
    association_id: int,
    event_service: EventService = Depends(get_event_service),
    current_user: User = Depends(get_current_active_user),
):
    """Remove an association from an event."""
    event_service.remove_association_from_event(event_id, association_id)

from typing import List, Optional
import csv
import io

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from app.core.auth import require_admin, require_viewer_or_above
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
    current_user: User = Depends(require_admin),
):
    """Create a new event."""
    return event_service.create_event(event)


@router.get("/", response_model=List[EventWithCalculationsAndDetails])
async def get_events(
    skip: int = 0,
    limit: int = Query(100, le=1000),  # Limit max to prevent overload
    status_filter: Optional[EventStatus] = Query(None, alias="status"),
    event_service: EventService = Depends(get_event_service),
    current_user: User = Depends(require_viewer_or_above),
):
    """Get events with pagination and optional status filter."""
    return event_service.get_events(skip=skip, limit=limit, status_filter=status_filter)


@router.get("/{event_id}", response_model=EventWithCalculationsAndDetails)
async def get_event(
    event_id: int,
    event_service: EventService = Depends(get_event_service),
    current_user: User = Depends(require_viewer_or_above),
):
    """Get single event with details."""
    return event_service.get_event_by_id(event_id)


@router.put("/{event_id}", response_model=EventWithCalculationsAndDetails)
async def update_event(
    event_id: int,
    event_update: EventUpdate,
    event_service: EventService = Depends(get_event_service),
    current_user: User = Depends(require_admin),
):
    """Update an existing event."""
    return event_service.update_event(event_id, event_update)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    event_service: EventService = Depends(get_event_service),
    current_user: User = Depends(require_admin),
):
    """Delete an event."""
    event_service.delete_event(event_id)


@router.post("/{event_id}/associations", status_code=status.HTTP_201_CREATED)
async def assign_association_to_event(
    event_id: int,
    association_data: EventAssociationCreate,
    event_service: EventService = Depends(get_event_service),
    current_user: User = Depends(require_admin),
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
    current_user: User = Depends(require_admin),
):
    """Remove an association from an event."""
    event_service.remove_association_from_event(event_id, association_id)


@router.get("/export/csv")
async def export_events_csv(
    skip: int = 0,
    limit: int = Query(1000, le=1000),
    status_filter: Optional[EventStatus] = Query(None, alias="status"),
    event_service: EventService = Depends(get_event_service),
    current_user: User = Depends(require_viewer_or_above),
):
    """Export events to CSV format."""
    events = event_service.get_events(
        skip=skip, limit=limit, status_filter=status_filter
    )

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # CSV headers
    headers = [
        "Nome",
        "Luogo",
        "Data Montaggio",
        "Data Smontaggio",
        "Date Evento",
        "Richiedente",
        "Metri Quadri",
        "Associazioni Assegnate",
        "Stato",
    ]
    writer.writerow(headers)

    # CSV data rows
    for event in events:
        # Format dates
        assembly_date = (
            event.assembly_datetime.strftime("%d/%m/%Y %H:%M")
            if event.assembly_datetime
            else ""
        )
        disassembly_date = (
            event.disassembly_datetime.strftime("%d/%m/%Y %H:%M")
            if event.disassembly_datetime
            else ""
        )

        # Format event dates
        start_date = (
            event.start_datetime.strftime("%d/%m/%Y %H:%M")
            if event.start_datetime
            else ""
        )
        end_date = (
            event.end_datetime.strftime("%d/%m/%Y %H:%M") if event.end_datetime else ""
        )
        event_dates = f"{start_date} - {end_date}" if end_date else start_date

        # Format associations with volunteer count
        associations_text = ""
        if event.event_associations:
            associations_list = []
            for assoc in event.event_associations:
                associations_list.append(
                    f"{assoc.association_name} ({assoc.volunteer_count} volontari)"
                )
            associations_text = "; ".join(associations_list)

        # Translate status
        status_translations = {
            EventStatus.TO_BE_SCHEDULED: "Da programmare",
            EventStatus.CONTRIBUTION_RECEIVED: "Contributo ricevuto",
            EventStatus.CERTIFIED_ASSEMBLY: "Montaggio certificato",
            EventStatus.CONTRIBUTION_PAID_TO_ASSOCIATION: "Contributo pagato all'associazione",
            EventStatus.COMPLETED: "Completato",
        }
        status_text = status_translations.get(event.status, event.status)

        row = [
            event.title,
            event.location,
            assembly_date,
            disassembly_date,
            event_dates,
            event.requester,
            event.stage_size,
            associations_text,
            status_text,
        ]
        writer.writerow(row)

    # Prepare the response
    output.seek(0)
    response = StreamingResponse(
        io.BytesIO(
            output.getvalue().encode("utf-8-sig")
        ),  # UTF-8 BOM for Excel compatibility
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=eventi.csv"},
    )

    return response

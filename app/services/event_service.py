from typing import Dict, List, Optional

from app.core.exceptions import BusinessLogicException, NotFoundException
from app.models import Event, EventAssociation, EventVolunteer, Volunteer
from app.models.event import EventStatus
from app.schemas.event import (
    EventAssociationCreate,
    EventAssociationDetail,
    EventCreate,
    EventUpdate,
    EventVolunteerDetail,
    EventWithCalculationsAndDetails,
)
from app.services.cost_calculator import CostCalculatorLegacy
from app.services.database import DatabaseService


class EventService:
    """Service layer for event-related business logic."""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.cost_calculator = CostCalculatorLegacy()

    def get_events(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[EventStatus] = None,
    ) -> List[EventWithCalculationsAndDetails]:
        """Get events with calculations and details."""
        events = self.db_service.get_events_with_associations(
            skip=skip, limit=limit, status_filter=status_filter
        )

        return [self._build_event_with_details(event) for event in events]

    def get_event_by_id(self, event_id: int) -> EventWithCalculationsAndDetails:
        """Get single event with details."""
        event = self.db_service.get_event_by_id_with_details(event_id)
        if not event:
            raise NotFoundException(f"🔍 Evento con ID {event_id} non trovato")

        return self._build_event_with_details(event)

    def create_event(self, event_data: EventCreate) -> EventWithCalculationsAndDetails:
        """Create a new event."""
        event = Event(**event_data.model_dump())
        created_event = self.db_service.create(event)
        return self._build_event_with_details(created_event)

    def update_event(
        self, event_id: int, event_data: EventUpdate
    ) -> EventWithCalculationsAndDetails:
        """Update an existing event."""
        event = self.db_service.get_event_by_id_with_details(event_id)
        if not event:
            raise NotFoundException(f"🔍 Evento con ID {event_id} non trovato")

        update_data = event_data.model_dump(exclude_unset=True)
        updated_event = self.db_service.update(event, update_data)
        return self._build_event_with_details(updated_event)

    def delete_event(self, event_id: int) -> bool:
        """Delete an event."""
        event = self.db_service.get_event_by_id_with_details(event_id)
        if not event:
            raise NotFoundException(f"🔍 Evento con ID {event_id} non trovato")

        return self.db_service.delete(event)

    def assign_association_to_event(
        self, event_id: int, assignment_data: EventAssociationCreate
    ) -> Dict[str, str]:
        """Assign an association to an event with volunteers."""
        # Check if event exists
        event = self.db_service.get_event_by_id_with_details(event_id)
        if not event:
            raise NotFoundException(f"🔍 Evento con ID {event_id} non trovato")

        # Check if association exists
        association = self.db_service.get_association_by_id(
            assignment_data.association_id
        )
        if not association:
            raise NotFoundException(
                f"🔍 Associazione con ID {assignment_data.association_id} non trovata"
            )

        # Check if already assigned
        existing = self.db_service.get_event_association(
            event_id, assignment_data.association_id
        )
        
        if existing:
            # Update existing association instead of throwing error
            update_data = {
                "volunteer_count": assignment_data.volunteer_count
            }
            updated_association = self.db_service.update(existing, update_data)
            
            # Remove existing volunteer assignments
            from app.models import EventVolunteer
            self.db_service.db.query(EventVolunteer).filter(
                EventVolunteer.event_association_id == existing.id
            ).delete()
            self.db_service.db.commit()
            
            # Assign new volunteers if provided
            if assignment_data.volunteer_ids:
                self._assign_volunteers_to_event(
                    updated_association.id,
                    assignment_data.volunteer_ids,
                    assignment_data.association_id,
                )
            
            return {"message": "✅ Associazione aggiornata nell'evento con successo"}
        else:
            # Create new event association
            event_association = EventAssociation(
                event_id=event_id,
                association_id=assignment_data.association_id,
                volunteer_count=assignment_data.volunteer_count,
            )
            created_association = self.db_service.create(event_association)

            # Assign specific volunteers if provided
            if assignment_data.volunteer_ids:
                self._assign_volunteers_to_event(
                    created_association.id,
                    assignment_data.volunteer_ids,
                    assignment_data.association_id,
                )

            return {"message": "✅ Associazione assegnata all'evento con successo"}

    def remove_association_from_event(self, event_id: int, association_id: int) -> bool:
        """Remove an association from an event."""
        event_association = self.db_service.get_event_association(
            event_id, association_id
        )
        if not event_association:
            raise NotFoundException("⚠️ Associazione non assegnata a questo evento")

        return self.db_service.delete(event_association)

    def _assign_volunteers_to_event(
        self, event_association_id: int, volunteer_ids: List[int], association_id: int
    ) -> None:
        """Assign specific volunteers to an event association."""
        volunteers = []

        for volunteer_id in volunteer_ids:
            # Verify volunteer belongs to the association
            volunteer = (
                self.db_service.db.query(Volunteer)
                .filter(
                    Volunteer.id == volunteer_id,
                    Volunteer.association_id == association_id,
                )
                .first()
            )

            if volunteer:
                event_volunteer = EventVolunteer(
                    event_association_id=event_association_id, volunteer_id=volunteer_id
                )
                volunteers.append(event_volunteer)

        if volunteers:
            self.db_service.bulk_create(volunteers)

    def _build_event_with_details(
        self, event: Event
    ) -> EventWithCalculationsAndDetails:
        """Build event response with calculations and association details."""
        # Calculate costs
        total_cost = self.cost_calculator.calculate_event_cost(event.stage_size)
        pro_loco_share = self.cost_calculator.calculate_pro_loco_share(total_cost)
        certification_cost = self.cost_calculator.get_certification_cost()

        # Build association details
        event_associations = []
        for ea in event.event_associations:
            # Get volunteer details
            volunteers = []
            for ev in ea.volunteers:
                volunteers.append(
                    EventVolunteerDetail(
                        id=ev.id,
                        volunteer_id=ev.volunteer.id,
                        volunteer_name=f"{ev.volunteer.first_name} {ev.volunteer.last_name}",
                        is_certified=ev.volunteer.is_certified,
                    )
                )

            event_associations.append(
                EventAssociationDetail(
                    id=ea.id,
                    event_id=ea.event_id,
                    association_id=ea.association_id,
                    volunteer_count=ea.volunteer_count,
                    association_name=ea.association.name,
                    volunteers=volunteers,
                )
            )

        return EventWithCalculationsAndDetails(
            id=event.id,
            title=event.title,
            start_datetime=event.start_datetime,
            end_datetime=event.end_datetime,
            location=event.location,
            stage_size=event.stage_size,
            requester=event.requester,
            request_received_date=event.request_received_date,
            assembly_datetime=event.assembly_datetime,
            disassembly_datetime=event.disassembly_datetime,
            status=event.status,
            event_associations=event_associations,
            total_cost=total_cost,
            pro_loco_share=pro_loco_share,
            certification_cost=certification_cost,
        )

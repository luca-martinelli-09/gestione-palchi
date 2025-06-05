from typing import List

from app.core.exceptions import BusinessLogicException, NotFoundException
from app.models import Association, Volunteer
from app.schemas.association import Association as AssociationSchema
from app.schemas.association import AssociationCreate, AssociationUpdate
from app.schemas.association import Volunteer as VolunteerSchema
from app.schemas.association import VolunteerCreate, VolunteerUpdate
from app.services.database import DatabaseService


class AssociationService:
    """Service layer for association-related business logic."""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    def get_associations(
        self, skip: int = 0, limit: int = 100
    ) -> List[AssociationSchema]:
        """Get associations with their volunteers."""
        associations = self.db_service.get_associations_with_volunteers(skip, limit)
        return [AssociationSchema.model_validate(assoc) for assoc in associations]

    def get_association_by_id(self, association_id: int) -> AssociationSchema:
        """Get association by ID."""
        association = self.db_service.get_association_by_id(association_id)
        if not association:
            raise NotFoundException(f"🔍 Associazione con ID {association_id} non trovata")

        return AssociationSchema.model_validate(association)

    def create_association(
        self, association_data: AssociationCreate
    ) -> AssociationSchema:
        """Create a new association."""
        # Check if association with same name already exists
        existing = (
            self.db_service.db.query(Association)
            .filter(Association.name == association_data.name)
            .first()
        )

        if existing:
            raise BusinessLogicException(
                f"⚠️ Associazione con nome '{association_data.name}' già esistente"
            )

        association = Association(**association_data.model_dump())
        created_association = self.db_service.create(association)
        return AssociationSchema.model_validate(created_association)

    def update_association(
        self, association_id: int, association_data: AssociationUpdate
    ) -> AssociationSchema:
        """Update an existing association."""
        association = self.db_service.get_association_by_id(association_id)
        if not association:
            raise NotFoundException(f"🔍 Associazione con ID {association_id} non trovata")

        update_data = association_data.model_dump(exclude_unset=True)

        # Check name uniqueness if name is being updated
        if "name" in update_data:
            existing = (
                self.db_service.db.query(Association)
                .filter(
                    Association.name == update_data["name"],
                    Association.id != association_id,
                )
                .first()
            )

            if existing:
                raise BusinessLogicException(
                    f"⚠️ Associazione con nome '{update_data['name']}' già esistente"
                )

        updated_association = self.db_service.update(association, update_data)
        return AssociationSchema.model_validate(updated_association)

    def delete_association(self, association_id: int) -> bool:
        """Delete an association."""
        association = self.db_service.get_association_by_id(association_id)
        if not association:
            raise NotFoundException(f"🔍 Associazione con ID {association_id} non trovata")

        # Check if association has events assigned
        from app.models import EventAssociation

        event_count = (
            self.db_service.db.query(EventAssociation)
            .filter(EventAssociation.association_id == association_id)
            .count()
        )

        if event_count > 0:
            raise BusinessLogicException(
                f"❌ Impossibile eliminare l'associazione: ha {event_count} eventi assegnati. "
                "Rimuovere prima le assegnazioni degli eventi."
            )

        return self.db_service.delete(association)

    # Volunteer methods
    def get_association_volunteers(self, association_id: int) -> List[VolunteerSchema]:
        """Get volunteers for a specific association."""
        # Verify association exists
        association = self.db_service.get_association_by_id(association_id)
        if not association:
            raise NotFoundException(f"🔍 Associazione con ID {association_id} non trovata")

        volunteers = self.db_service.get_association_volunteers(association_id)
        return [VolunteerSchema.model_validate(volunteer) for volunteer in volunteers]

    def create_volunteer(
        self, association_id: int, volunteer_data: VolunteerCreate
    ) -> VolunteerSchema:
        """Create a new volunteer for an association."""
        # Verify association exists
        association = self.db_service.get_association_by_id(association_id)
        if not association:
            raise NotFoundException(f"🔍 Associazione con ID {association_id} non trovata")

        volunteer = Volunteer(
            association_id=association_id, **volunteer_data.model_dump()
        )
        created_volunteer = self.db_service.create(volunteer)
        return VolunteerSchema.model_validate(created_volunteer)

    def update_volunteer(
        self, association_id: int, volunteer_id: int, volunteer_data: VolunteerUpdate
    ) -> VolunteerSchema:
        """Update an existing volunteer."""
        volunteer = (
            self.db_service.db.query(Volunteer)
            .filter(
                Volunteer.id == volunteer_id, Volunteer.association_id == association_id
            )
            .first()
        )

        if not volunteer:
            raise NotFoundException(
                f"🔍 Volontario con ID {volunteer_id} non trovato nell'associazione {association_id}"
            )

        update_data = volunteer_data.model_dump(exclude_unset=True)
        updated_volunteer = self.db_service.update(volunteer, update_data)
        return VolunteerSchema.model_validate(updated_volunteer)

    def delete_volunteer(self, association_id: int, volunteer_id: int) -> bool:
        """Delete a volunteer."""
        volunteer = (
            self.db_service.db.query(Volunteer)
            .filter(
                Volunteer.id == volunteer_id, Volunteer.association_id == association_id
            )
            .first()
        )

        if not volunteer:
            raise NotFoundException(
                f"🔍 Volontario con ID {volunteer_id} non trovato nell'associazione {association_id}"
            )

        # Check if volunteer is assigned to any events
        from app.models import EventVolunteer

        event_assignments = (
            self.db_service.db.query(EventVolunteer)
            .filter(EventVolunteer.volunteer_id == volunteer_id)
            .count()
        )

        if event_assignments > 0:
            raise BusinessLogicException(
                f"❌ Impossibile eliminare il volontario: è assegnato a {event_assignments} eventi. "
                "Rimuovere prima le assegnazioni degli eventi."
            )

        return self.db_service.delete(volunteer)

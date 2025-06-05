from typing import List

from fastapi import APIRouter, Depends, Query, status

from app.core.auth import get_current_active_user
from app.models.auth import User
from app.schemas.association import Association as AssociationSchema
from app.schemas.association import AssociationCreate, AssociationUpdate
from app.schemas.association import Volunteer as VolunteerSchema
from app.schemas.association import VolunteerCreate, VolunteerUpdate
from app.services.association_service import AssociationService
from app.services.database import DatabaseService, get_database_service

router = APIRouter()


def get_association_service(
    db_service: DatabaseService = Depends(get_database_service),
) -> AssociationService:
    """Dependency to get association service instance."""
    return AssociationService(db_service)


@router.post("/", response_model=AssociationSchema, status_code=status.HTTP_201_CREATED)
async def create_association(
    association: AssociationCreate,
    association_service: AssociationService = Depends(get_association_service),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new association."""
    return association_service.create_association(association)


@router.get("/", response_model=List[AssociationSchema])
async def get_associations(
    skip: int = 0,
    limit: int = Query(100, le=1000),  # Limit max to prevent overload
    association_service: AssociationService = Depends(get_association_service),
    current_user: User = Depends(get_current_active_user),
):
    """Get associations with pagination."""
    return association_service.get_associations(skip=skip, limit=limit)


@router.get("/{association_id}", response_model=AssociationSchema)
async def get_association(
    association_id: int,
    association_service: AssociationService = Depends(get_association_service),
    current_user: User = Depends(get_current_active_user),
):
    """Get association by ID."""
    return association_service.get_association_by_id(association_id)


@router.put("/{association_id}", response_model=AssociationSchema)
async def update_association(
    association_id: int,
    association_update: AssociationUpdate,
    association_service: AssociationService = Depends(get_association_service),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing association."""
    return association_service.update_association(association_id, association_update)


@router.delete("/{association_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_association(
    association_id: int,
    association_service: AssociationService = Depends(get_association_service),
    current_user: User = Depends(get_current_active_user),
):
    """Delete an association."""
    association_service.delete_association(association_id)


# Volunteer endpoints
@router.get("/{association_id}/volunteers", response_model=List[VolunteerSchema])
async def get_association_volunteers(
    association_id: int,
    association_service: AssociationService = Depends(get_association_service),
    current_user: User = Depends(get_current_active_user),
):
    """Get volunteers for a specific association."""
    return association_service.get_association_volunteers(association_id)


@router.post(
    "/{association_id}/volunteers",
    response_model=VolunteerSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_volunteer(
    association_id: int,
    volunteer: VolunteerCreate,
    association_service: AssociationService = Depends(get_association_service),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new volunteer for an association."""
    return association_service.create_volunteer(association_id, volunteer)


@router.put(
    "/{association_id}/volunteers/{volunteer_id}", response_model=VolunteerSchema
)
async def update_volunteer(
    association_id: int,
    volunteer_id: int,
    volunteer_update: VolunteerUpdate,
    association_service: AssociationService = Depends(get_association_service),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing volunteer."""
    return association_service.update_volunteer(
        association_id, volunteer_id, volunteer_update
    )


@router.delete(
    "/{association_id}/volunteers/{volunteer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_volunteer(
    association_id: int,
    volunteer_id: int,
    association_service: AssociationService = Depends(get_association_service),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a volunteer."""
    association_service.delete_volunteer(association_id, volunteer_id)

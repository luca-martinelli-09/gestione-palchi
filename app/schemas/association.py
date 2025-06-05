from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class VolunteerBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    is_certified: bool = False


class VolunteerCreate(VolunteerBase):
    pass


class VolunteerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    is_certified: Optional[bool] = None


class Volunteer(VolunteerBase):
    id: int
    association_id: int

    class Config:
        from_attributes = True


class AssociationBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    tax_code: Optional[str] = None
    iban: Optional[str] = None
    headquarters: Optional[str] = None


class AssociationCreate(AssociationBase):
    pass


class AssociationUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    tax_code: Optional[str] = None
    iban: Optional[str] = None
    headquarters: Optional[str] = None


class Association(AssociationBase):
    id: int
    volunteers: List[Volunteer] = []

    class Config:
        from_attributes = True

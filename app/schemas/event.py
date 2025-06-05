from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.event import EventStatus


class EventBase(BaseModel):
    title: str
    start_datetime: datetime
    end_datetime: datetime
    location: str
    stage_size: float
    requester: str
    request_received_date: datetime
    assembly_datetime: Optional[datetime] = None
    disassembly_datetime: Optional[datetime] = None
    status: EventStatus = EventStatus.TO_BE_SCHEDULED


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    location: Optional[str] = None
    stage_size: Optional[float] = None
    requester: Optional[str] = None
    request_received_date: Optional[datetime] = None
    assembly_datetime: Optional[datetime] = None
    disassembly_datetime: Optional[datetime] = None
    status: Optional[EventStatus] = None


class EventAssociationBase(BaseModel):
    association_id: int
    volunteer_count: int


class EventAssociationCreate(EventAssociationBase):
    volunteer_ids: Optional[List[int]] = []


class EventVolunteerDetail(BaseModel):
    id: int
    volunteer_id: int
    volunteer_name: str
    is_certified: bool

    class Config:
        from_attributes = True


class EventAssociationDetail(EventAssociationBase):
    id: int
    event_id: int
    association_name: str
    volunteers: List[EventVolunteerDetail] = []

    class Config:
        from_attributes = True


class EventAssociation(EventAssociationBase):
    id: int
    event_id: int

    class Config:
        from_attributes = True


class Event(EventBase):
    id: int
    event_associations: List[EventAssociation] = []

    class Config:
        from_attributes = True


class EventWithDetails(EventBase):
    id: int
    event_associations: List[EventAssociationDetail] = []

    class Config:
        from_attributes = True


class EventWithCalculations(Event):
    total_cost: float
    pro_loco_share: float
    certification_cost: float


class EventWithCalculationsAndDetails(EventBase):
    id: int
    event_associations: List[EventAssociationDetail] = []
    total_cost: float
    pro_loco_share: float
    certification_cost: float

    class Config:
        from_attributes = True

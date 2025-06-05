import enum

from sqlalchemy import (Column, DateTime, Enum, Float, ForeignKey, Integer,
                        String)
from sqlalchemy.orm import relationship

from app.database.base import Base


class EventStatus(enum.Enum):
    TO_BE_SCHEDULED = "To Be Scheduled"
    CONTRIBUTION_RECEIVED = "Contribution Received"
    CERTIFIED_ASSEMBLY = "Certified Assembly"
    CONTRIBUTION_PAID_TO_ASSOCIATION = "Contribution Paid to Association"
    COMPLETED = "Completed"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    location = Column(String, nullable=False)
    stage_size = Column(Float, nullable=False)
    status = Column(Enum(EventStatus), default=EventStatus.TO_BE_SCHEDULED)
    requester = Column(String, nullable=False)
    assembly_datetime = Column(DateTime, nullable=True)
    disassembly_datetime = Column(DateTime, nullable=True)
    request_received_date = Column(DateTime, nullable=False)

    event_associations = relationship(
        "EventAssociation", back_populates="event", cascade="all, delete-orphan"
    )


class EventAssociation(Base):
    __tablename__ = "event_associations"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    association_id = Column(Integer, ForeignKey("associations.id"))
    volunteer_count = Column(Integer, nullable=False, default=0)

    event = relationship("Event", back_populates="event_associations")
    association = relationship("Association", back_populates="event_associations")
    volunteers = relationship(
        "EventVolunteer",
        back_populates="event_association",
        cascade="all, delete-orphan",
    )


class EventVolunteer(Base):
    __tablename__ = "event_volunteers"

    id = Column(Integer, primary_key=True, index=True)
    event_association_id = Column(Integer, ForeignKey("event_associations.id"))
    volunteer_id = Column(Integer, ForeignKey("volunteers.id"))

    event_association = relationship("EventAssociation", back_populates="volunteers")
    volunteer = relationship("Volunteer")

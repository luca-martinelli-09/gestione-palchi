from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.base import Base


class Association(Base):
    __tablename__ = "associations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    contact_person = Column(String, nullable=True)
    tax_code = Column(String, nullable=True)
    iban = Column(String, nullable=True)
    headquarters = Column(String, nullable=True)

    volunteers = relationship(
        "Volunteer", back_populates="association", cascade="all, delete-orphan"
    )
    event_associations = relationship("EventAssociation", back_populates="association")


class Volunteer(Base):
    __tablename__ = "volunteers"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    is_certified = Column(Boolean, default=False)
    association_id = Column(Integer, ForeignKey("associations.id"))

    association = relationship("Association", back_populates="volunteers")

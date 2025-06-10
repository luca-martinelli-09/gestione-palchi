from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.database.base import get_db
from app.models.auth import User
from app.models import Association, Event, EventAssociation
from app.models.event import EventStatus
from app.schemas.reports import (
    AssociationEarnings,
    EventEarningsDetail,
    OverallTotals,
    ProLocoEarnings,
    ReportsResponse,
)
from app.services.cost_calculator import CostCalculatorLegacy as CostCalculator

router = APIRouter()


@router.get("/", response_model=ReportsResponse)
async def get_reports(
    status_filter: Optional[EventStatus] = Query(None, alias="status"),
    include_details: bool = Query(
        False, description="Include detailed earnings per event"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    # Base query for events
    events_query = db.query(Event)
    if status_filter:
        events_query = events_query.filter(Event.status == status_filter)

    events = events_query.all()

    # Calculate totals
    total_events = len(events)
    total_revenue = 0
    total_pro_loco_earnings = 0
    total_certification_costs = total_events * CostCalculator.get_certification_cost()

    # Association earnings tracking
    association_earnings_dict = {}
    events_with_earnings = []

    for event in events:
        event_cost = CostCalculator.calculate_event_cost(event.stage_size)
        pro_loco_share = CostCalculator.calculate_pro_loco_share(event_cost)
        certification_cost = CostCalculator.get_certification_cost()

        total_revenue += event_cost
        total_pro_loco_earnings += pro_loco_share

        # Get event associations
        event_associations = (
            db.query(EventAssociation)
            .filter(EventAssociation.event_id == event.id)
            .all()
        )

        total_volunteers = sum(ea.volunteer_count for ea in event_associations)
        event_associations_details = []

        for ea in event_associations:
            association = (
                db.query(Association)
                .filter(Association.id == ea.association_id)
                .first()
            )
            if association:
                earnings = CostCalculator.calculate_association_earnings(
                    event_cost, pro_loco_share, ea.volunteer_count, total_volunteers
                )

                # Track association earnings
                if ea.association_id not in association_earnings_dict:
                    association_earnings_dict[ea.association_id] = {
                        "name": association.name,
                        "total_earnings": 0,
                        "events_count": 0,
                    }

                association_earnings_dict[ea.association_id][
                    "total_earnings"
                ] += earnings
                association_earnings_dict[ea.association_id]["events_count"] += 1

                event_associations_details.append(
                    {
                        "association_id": ea.association_id,
                        "association_name": association.name,
                        "volunteer_count": ea.volunteer_count,
                        "earnings": earnings,
                    }
                )

        if include_details:
            events_with_earnings.append(
                EventEarningsDetail(
                    event_id=event.id,
                    event_title=event.title,
                    total_cost=event_cost,
                    pro_loco_share=pro_loco_share,
                    certification_cost=certification_cost,
                    associations=event_associations_details,
                )
            )

    # Prepare association earnings list
    association_earnings = [
        AssociationEarnings(
            association_id=assoc_id,
            association_name=data["name"],
            total_earnings=data["total_earnings"],
            events_count=data["events_count"],
        )
        for assoc_id, data in association_earnings_dict.items()
    ]

    total_association_earnings = sum(ae.total_earnings for ae in association_earnings)

    # Prepare response
    response = ReportsResponse(
        association_earnings=association_earnings,
        pro_loco_earnings=ProLocoEarnings(
            total_earnings=total_pro_loco_earnings, events_count=total_events
        ),
        overall_totals=OverallTotals(
            total_events=total_events,
            total_revenue=total_revenue,
            total_pro_loco_earnings=total_pro_loco_earnings,
            total_association_earnings=total_association_earnings,
            total_certification_costs=total_certification_costs,
        ),
        events_with_earnings=events_with_earnings if include_details else None,
    )

    return response


@router.get(
    "/associations/{association_id}/earnings", response_model=AssociationEarnings
)
async def get_association_earnings(
    association_id: int,
    status_filter: Optional[EventStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    # Verify association exists
    association = db.query(Association).filter(Association.id == association_id).first()
    if not association:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="🔍 Associazione non trovata"
        )

    # Get events for this association
    query = (
        db.query(Event)
        .join(EventAssociation)
        .filter(EventAssociation.association_id == association_id)
    )

    if status_filter:
        query = query.filter(Event.status == status_filter)

    events = query.all()

    total_earnings = 0
    events_count = len(events)

    for event in events:
        event_cost = CostCalculator.calculate_event_cost(event.stage_size)
        pro_loco_share = CostCalculator.calculate_pro_loco_share(event_cost)

        # Get this association's contribution to the event
        event_association = (
            db.query(EventAssociation)
            .filter(
                EventAssociation.event_id == event.id,
                EventAssociation.association_id == association_id,
            )
            .first()
        )

        if event_association:
            # Calculate total volunteers for this event
            total_volunteers = (
                db.query(func.sum(EventAssociation.volunteer_count))
                .filter(EventAssociation.event_id == event.id)
                .scalar()
                or 0
            )

            earnings = CostCalculator.calculate_association_earnings(
                event_cost,
                pro_loco_share,
                event_association.volunteer_count,
                total_volunteers,
            )
            total_earnings += earnings

    return AssociationEarnings(
        association_id=association_id,
        association_name=association.name,
        total_earnings=total_earnings,
        events_count=events_count,
    )


@router.get("/pro-loco/earnings", response_model=ProLocoEarnings)
async def get_pro_loco_earnings(
    status_filter: Optional[EventStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    events_query = db.query(Event)
    if status_filter:
        events_query = events_query.filter(Event.status == status_filter)

    events = events_query.all()

    total_earnings = 0
    events_count = len(events)

    for event in events:
        event_cost = CostCalculator.calculate_event_cost(event.stage_size)
        pro_loco_share = CostCalculator.calculate_pro_loco_share(event_cost)
        total_earnings += pro_loco_share

    return ProLocoEarnings(total_earnings=total_earnings, events_count=events_count)

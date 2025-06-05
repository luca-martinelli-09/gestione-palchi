from typing import List, Optional

from pydantic import BaseModel


class AssociationEarnings(BaseModel):
    association_id: int
    association_name: str
    total_earnings: float
    events_count: int


class ProLocoEarnings(BaseModel):
    total_earnings: float
    events_count: int


class OverallTotals(BaseModel):
    total_events: int
    total_revenue: float
    total_pro_loco_earnings: float
    total_association_earnings: float
    total_certification_costs: float


class EventEarningsDetail(BaseModel):
    event_id: int
    event_title: str
    total_cost: float
    pro_loco_share: float
    certification_cost: float
    associations: List[dict]


class ReportsResponse(BaseModel):
    association_earnings: List[AssociationEarnings]
    pro_loco_earnings: ProLocoEarnings
    overall_totals: OverallTotals
    events_with_earnings: Optional[List[EventEarningsDetail]] = None

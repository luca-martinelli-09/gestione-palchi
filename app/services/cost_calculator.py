from functools import lru_cache
from typing import Dict

from app.core.config import Settings, get_settings


class CostCalculator:
    """Optimized calculator for event costs and Pro Loco shares with caching"""

    def __init__(self, settings: Settings = None):
        self.settings = settings or get_settings()

    @lru_cache(maxsize=1000)
    def calculate_event_cost(self, stage_size: float) -> float:
        """
        Calculate event cost based on stage size (cached).
        Formula: 100 + (stage_size * cost_per_sqm)
        - cost_per_sqm = 6 if stage_size <= 70
        - cost_per_sqm = 5.5 if stage_size > 70
        Result is rounded to nearest ten.
        """
        base_cost = 100
        cost_per_sqm = 6 if stage_size <= 70 else 5.5
        total_cost = base_cost + (stage_size * cost_per_sqm)
        return round(total_cost / 10) * 10

    @lru_cache(maxsize=1000)
    def calculate_pro_loco_share(self, total_cost: float) -> float:
        """
        Calculate Pro Loco's share: 10% of total cost, rounded to nearest ten (cached).
        """
        pro_loco_percentage = total_cost * 0.10
        return round(pro_loco_percentage / 10) * 10

    def calculate_association_earnings(
        self,
        total_cost: float,
        pro_loco_share: float,
        association_volunteers: int,
        total_volunteers: int,
    ) -> float:
        """
        Calculate association earnings based on volunteer percentage.
        Formula: (total_cost - 50 - pro_loco_share) * (association_volunteers / total_volunteers)
        """
        if total_volunteers == 0:
            return 0.0

        available_amount = total_cost - self.get_certification_cost() - pro_loco_share
        volunteer_percentage = association_volunteers / total_volunteers
        return available_amount * volunteer_percentage

    def get_certification_cost(self) -> float:
        """Return the fixed certification cost per event."""
        return 50.0

    def calculate_detailed_breakdown(self, stage_size: float) -> Dict[str, float]:
        """Calculate detailed cost breakdown for an event"""
        total_cost = self.calculate_event_cost(stage_size)
        pro_loco_share = self.calculate_pro_loco_share(total_cost)
        certification_cost = self.get_certification_cost()

        cost_per_sqm = 6 if stage_size <= 70 else 5.5

        return {
            "stage_size": stage_size,
            "total_cost": total_cost,
            "pro_loco_share": pro_loco_share,
            "certification_cost": certification_cost,
            "available_for_associations": total_cost
            - pro_loco_share
            - certification_cost,
            "cost_per_sqm": cost_per_sqm,
            "base_cost": 100,
            "pro_loco_percentage": 0.10,
        }

    def clear_cache(self):
        """Clear calculation cache"""
        self.calculate_event_cost.cache_clear()
        self.calculate_pro_loco_share.cache_clear()


# Global instance
_cost_calculator = CostCalculator()


# Legacy static methods for backward compatibility
class CostCalculatorLegacy:
    @staticmethod
    def calculate_event_cost(stage_size: float) -> float:
        return _cost_calculator.calculate_event_cost(stage_size)

    @staticmethod
    def calculate_pro_loco_share(total_cost: float) -> float:
        return _cost_calculator.calculate_pro_loco_share(total_cost)

    @staticmethod
    def calculate_association_earnings(
        total_cost: float,
        pro_loco_share: float,
        association_volunteers: int,
        total_volunteers: int,
    ) -> float:
        return _cost_calculator.calculate_association_earnings(
            total_cost, pro_loco_share, association_volunteers, total_volunteers
        )

    @staticmethod
    def get_certification_cost() -> float:
        return _cost_calculator.get_certification_cost()


# Keep backward compatibility
CostCalculatorStatic = CostCalculatorLegacy

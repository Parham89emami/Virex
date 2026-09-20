from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VPNPlan:
    code: str
    name: str
    traffic_gb: int
    duration_days: int
    price_toman: int


class VPNService:
    @staticmethod
    def get_plans() -> list[VPNPlan]:
        return [
            VPNPlan("10gb", "10GB", 10, 30, 49_000),
            VPNPlan("20gb", "20GB", 20, 30, 68_000),
            VPNPlan("30gb", "30GB", 30, 30, 87_000),
            VPNPlan("40gb", "40GB", 40, 30, 106_000),
            VPNPlan("50gb", "50GB", 50, 30, 125_000),
            VPNPlan("60gb", "60GB", 60, 30, 144_000),
            VPNPlan("70gb", "70GB", 70, 30, 163_000),
            VPNPlan("80gb", "80GB", 80, 30, 182_000),
            VPNPlan("90gb", "90GB", 90, 30, 201_000),
            VPNPlan("100gb", "100GB", 100, 30, 220_000),
        ]

    @staticmethod
    def get_plan_by_code(code: str) -> VPNPlan | None:
        normalized_code = code.strip().lower()
        return next(
            (plan for plan in VPNService.get_plans() if plan.code == normalized_code),
            None,
        )

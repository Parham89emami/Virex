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
            VPNPlan("plan_10gb", "بیسیک 10 گیگ", 10, 30, 49000),
            VPNPlan("plan_20gb", "بیسیک 20 گیگ", 20, 30, 68000),
            VPNPlan("plan_30gb", "بیسیک 30 گیگ", 30, 30, 87000),
            VPNPlan("plan_40gb", "بیسیک 40 گیگ", 40, 30, 106000),
            VPNPlan("plan_50gb", "بیسیک 50 گیگ", 50, 30, 125000),
            VPNPlan("plan_60gb", "بیسیک 60 گیگ", 60, 30, 144000),
            VPNPlan("plan_70gb", "بیسیک 70 گیگ", 70, 30, 163000),
            VPNPlan("plan_80gb", "بیسیک 80 گیگ", 80, 30, 182000),
            VPNPlan("plan_90gb", "بیسیک 90 گیگ", 90, 30, 201000),
            VPNPlan("plan_100gb", "بیسیک 100 گیگ", 100, 30, 220000),
        ]

    @staticmethod
    def get_plan_by_code(code: str) -> VPNPlan | None:
        return next((plan for plan in VPNService.get_plans() if plan.code == code), None)

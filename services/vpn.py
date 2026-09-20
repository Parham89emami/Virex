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
            VPNPlan("plan_10gb", "اقتصادی", 10, 30, 49000),
            VPNPlan("plan_20gb", "معیاری", 20, 30, 68000),
            VPNPlan("plan_30gb", "حرفه‌ای", 30, 30, 87000),
            VPNPlan("plan_40gb", "استاندارد", 40, 30, 106000),
            VPNPlan("plan_50gb", "محبوب", 50, 30, 125000),
            VPNPlan("plan_60gb", "پیشرفته", 60, 30, 144000),
            VPNPlan("plan_70gb", "تجاری", 70, 30, 163000),
            VPNPlan("plan_80gb", "ویژه", 80, 30, 182000),
            VPNPlan("plan_90gb", "سازمانی", 90, 30, 201000),
            VPNPlan("plan_100gb", "طلایی", 100, 30, 220000),
        ]

    @staticmethod
    def get_plan_by_code(code: str) -> VPNPlan | None:
        return next((plan for plan in VPNService.get_plans() if plan.code == code), None)

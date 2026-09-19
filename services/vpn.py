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
            VPNPlan("basic", "اقتصادی", 10, 30, 280000),
            VPNPlan("standard", "استاندارد", 25, 60, 520000),
            VPNPlan("pro", "حرفه‌ای", 60, 90, 980000),
            VPNPlan("business", "سازمانی", 200, 180, 1760000),
        ]

    @staticmethod
    def get_plan_by_code(code: str) -> VPNPlan | None:
        return next((plan for plan in VPNService.get_plans() if plan.code == code), None)

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
            VPNPlan("basic", "اقتصادی", 10, 30, 49000),
            VPNPlan("standard20", "استاندارد", 20, 30, 68000),
            VPNPlan("standard30", "استاندارد", 30, 30, 87000),
            VPNPlan("pro40", "حرفه‌ای", 40, 30, 106000),
            VPNPlan("pro50", "حرفه‌ای", 50, 30, 125000),
            VPNPlan("pro60", "حرفه‌ای", 60, 30, 144000),
            VPNPlan("pro70", "حرفه‌ای", 70, 30, 163000),
            VPNPlan("pro80", "حرفه‌ای", 80, 30, 182000),
            VPNPlan("pro90", "حرفه‌ای", 90, 30, 201000),
            VPNPlan("premium100", "سازمانی", 100, 30, 220000),
        ]

    @staticmethod
    def get_plan_by_code(code: str) -> VPNPlan | None:
        return next((plan for plan in VPNService.get_plans() if plan.code == code), None)

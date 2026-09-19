from __future__ import annotations

import httpx

from config.settings import settings


class MarzbanService:
    def __init__(self) -> None:
        self.enabled = settings.marzban_enabled

    async def create_user(self, username: str, **kwargs: object) -> dict[str, object]:
        if not self.enabled:
            return {"enabled": False, "message": "ادغام مرزبان غیرفعال است."}
        if not settings.marzban_url:
            return {"enabled": True, "status": "error", "message": "MARZBAN_URL تنظیم نشده است."}
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(f"{settings.marzban_url.rstrip('/')}/api/users", json={"username": username, **kwargs}, auth=(settings.marzban_username, settings.marzban_password))
                response.raise_for_status()
                return {"enabled": True, "status": "success", "response": response.json()}
        except Exception as exc:
            return {"enabled": True, "status": "error", "message": str(exc)}

from __future__ import annotations

from config.settings import settings


class PaymentService:
    @staticmethod
    def payment_details() -> tuple[str, str]:
        return (settings.card_number or "در تنظیمات وارد نشده است", settings.card_owner or "در تنظیمات وارد نشده است")

    def payment_instructions(self, order_id: str, amount: int, plan_name: str | None = None, traffic_gb: int | None = None) -> str:
        card_number, card_owner = self.payment_details()
        plan_label = f"پلن: {plan_name}" if plan_name else "پلن: نامشخص"
        traffic_label = f"حجم: {traffic_gb} گیگ" if traffic_gb is not None else "حجم: نامشخص"
        return (
            "💳 اطلاعات پرداخت\n\n"
            f"شماره سفارش: {order_id}\n"
            f"{plan_label}\n"
            f"{traffic_label}\n"
            f"مبلغ: {amount:,} تومان\n\n"
            f"شماره کارت: {card_number}\n"
            f"صاحب کارت: {card_owner}\n\n"
            "✅ پس از پرداخت، عکس یا فایل رسید را همینجا ارسال کنید.\n"
            "📌 وضعیت سفارش بعد از بررسی مدیر تغییر می‌کند."
        )

    @staticmethod
    def get_status_label(status: str) -> str:
        mapping = {
            "pending": "در انتظار پرداخت",
            "pending_review": "در حال بررسی رسید",
            "approved": "تأیید شده",
            "rejected": "رد شده",
            "confirmed": "تأیید شده",
        }
        return mapping.get(status, status)

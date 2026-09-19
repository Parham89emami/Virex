from __future__ import annotations

from config.settings import settings


class PaymentService:
    def payment_instructions(self, order_id: str, amount: int) -> str:
        card_number = settings.card_number or "در تنظیمات وارد نشده است"
        card_owner = settings.card_owner or "در تنظیمات وارد نشده است"
        return (
            "💳 اطلاعات پرداخت کارت‌به‌کارت\n\n"
            f"شماره سفارش: {order_id}\nمبلغ: {amount:,} تومان\n\n"
            f"شماره کارت: {card_number}\nصاحب کارت: {card_owner}\n\n"
            "پس از پرداخت، تصویر یا فایل رسید را همین‌جا ارسال کنید."
        )

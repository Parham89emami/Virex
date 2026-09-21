from __future__ import annotations

from config.settings import settings


class PaymentService:
    @staticmethod
    def payment_instructions(order_id: str, amount: int) -> str:
        return (f"💳 اطلاعات پرداخت کارت‌به‌کارت Virex\n\nشماره سفارش: {order_id}\nمبلغ: {amount:,} تومان\n\n"
                f"شماره کارت: {settings.card_number or 'تنظیم نشده'}\nصاحب کارت: {settings.card_owner or 'تنظیم نشده'}\n\n"
                "پس از پرداخت، تصویر رسید را همین‌جا ارسال کنید.")

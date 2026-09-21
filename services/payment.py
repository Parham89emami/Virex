from __future__ import annotations
from config.settings import settings
class PaymentService:
    def payment_instructions(self, order_id: str, amount: int) -> str:
        return f"💳 اطلاعات پرداخت کارت‌به‌کارت\n\nشماره سفارش: {order_id}\nمبلغ: {amount:,} تومان\n\nشماره کارت: {settings.card_number or 'در تنظیمات وارد نشده است'}\nصاحب کارت: {settings.card_owner or 'در تنظیمات وارد نشده است'}\n\nپس از پرداخت، تصویر رسید را همین‌جا ارسال کنید."

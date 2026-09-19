# Virex Telegram VPN Sales Bot

ربات فروش VPN وایرکس با Python 3.11، `python-telegram-bot`، SQLAlchemy و SQLite.

## اجرا

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

مقادیر واقعی را فقط در `.env` محلی یا Environment Variables سرویس Railway قرار دهید. فایل `.env` در Git نادیده گرفته می‌شود.

## متغیرهای Railway

- `8790858646:AAFFrT_rdszQN0AVWLLjY6jPX9lM5HsiOVI`: 
- `7049023194`: 
- `DATABASE_URL`: به‌صورت پیش‌فرض `sqlite+aiosqlite:///./virex.db`
- `CARD_NUMBER` و `CARD_OWNER`: اطلاعات پرداخت
- `MARZBAN_ENABLED=false` برای نسخه اولیه؛ سایر متغیرهای Marzban در صورت فعال‌سازی

## استقرار در Railway

1. این مخزن را در Railway از GitHub انتخاب کنید.
2. متغیرهای بالا را در بخش Variables اضافه کنید.
3. Railway از `runtime.txt` و `railway.toml` استفاده می‌کند و با دستور زیر اجرا می‌کند:

```bash
python main.py
```

ربات با polling کار می‌کند و به دامنه عمومی نیاز ندارد. برای پایداری SQLite در Railway، در محیط production بعداً `DATABASE_URL` را به PostgreSQL تغییر دهید؛ لایه داده با SQLAlchemy جدا شده است.

## امکانات

`/start` کاربر را ثبت می‌کند و منوی فارسی را نمایش می‌دهد. خرید VPN، سفارش‌های من، رسید عکس/فایل، و وضعیت سفارش پشتیبانی می‌شود. ادمین‌ها با `/admin` سفارش‌های در انتظار بررسی را می‌بینند و با `/confirm ORDER_ID` یا `/reject ORDER_ID` اقدام می‌کنند.

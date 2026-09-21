# VPN King

ربات فارسی فروش VPN با محصولات، موجودی کانفیگ، پرداخت کارت‌به‌کارت و تحویل امن پس از تأیید مدیر.

## اجرا
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

## متغیرهای محیطی
`BOT_TOKEN`، `ADMIN_IDS`، `DATABASE_URL`، `CARD_NUMBER`، `CARD_OWNER` و `SUPPORT_CONTACT` را در Railway Variables تنظیم کنید. اطلاعات حساس در Git ذخیره نمی‌شود.

## پنل مدیریت
فقط شناسه‌های `ADMIN_IDS` به `/admin` دسترسی دارند. محصولات اولیه هنگام اولین اجرا ساخته می‌شوند. برای جلوگیری از تحویل تکراری، اختصاص کانفیگ با یک تراکنش و شرط اتمیک وضعیت `available` انجام می‌شود.

Railway با `Procfile` یا `railway.toml` و دستور `python main.py` اجرا می‌شود.

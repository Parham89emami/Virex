# Virex

ربات فارسی فروش کانفیگ VPN با محصولات دیتابیسی، پرداخت کارت‌به‌کارت، کیف پول، کوپن، رسید و تحویل امن کانفیگ.

## اجرا

```bash
pip install -r requirements.txt
cp .env.example .env
python main.py
```

## Railway

`railway.toml` و `Procfile` هر دو `python main.py` را اجرا می‌کنند. برای محیط واقعی Railway یک سرویس PostgreSQL بسازید و مقدار `DATABASE_URL` سرویس Postgres را به سرویس Bot متصل کنید.

### Environment Variables

- `BOT_TOKEN`: توکن BotFather
- `ADMIN_IDS`: شناسه عددی مدیران، جداشده با کاما
- `DATABASE_URL`: مقدار اتصال PostgreSQL در Railway؛ SQLite فقط برای توسعه است
- `CARD_NUMBER`: شماره کارت دریافت وجه
- `CARD_OWNER`: نام صاحب کارت
- `SUPPORT_CONTACT`: آیدی پشتیبانی؛ مقدار پیشنهادی `@Parham88e`
- `LOG_LEVEL`: معمولاً `INFO`

## دستورات مدیر

- `/admin` گزارش فروش و موجودی
- `/products`، `/addproduct نام حجم مدت قیمت`، `/editproduct شناسه حجم مدت قیمت`
- `/toggleproduct شناسه`، `/deleteproduct شناسه`
- `/addconfig شناسه_محصول متن_کانفیگ`، `/configs`، `/deleteconfig شناسه`
- `/confirm شناسه_داخلی` و `/reject شناسه_داخلی`
- `/coupon کد percent|amount مقدار [سقف]`
- `/walletadd شناسه_تلگرام مبلغ`
- `/user شناسه_تلگرام`، `/block شناسه_تلگرام`، `/unblock شناسه_تلگرام`

محصولات پیش‌فرض Virex: 5GB/30,000، 10GB/60,000، 20GB/120,000، 50GB/200,000 و 100GB/345,000 تومان؛ همه ۳۰ روزه هستند.

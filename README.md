# Virex

ربات فارسی فروش کانفیگ VPN با محصولات دیتابیسی، پرداخت کارت‌به‌کارت، کیف پول، رسید و تحویل امن کانفیگ.

## اجرا

```bash
pip install -r requirements.txt
cp .env.example .env
python main.py
```

## Railway

سرویس Railway باید به‌صورت یک instance اجرا شود، چون Telegram polling برای هر bot token فقط یک مصرف‌کننده هم‌زمان می‌پذیرد. Virex علاوه بر آن، در صورت استفاده از PostgreSQL یک advisory lock دیتابیسی می‌گیرد و از شروع polling دوم جلوگیری می‌کند.

### Start Command

```bash
python main.py
```

این دستور در `railway.toml` و `Procfile` تنظیم شده است.

### Environment Variables

- `BOT_TOKEN`: توکن BotFather
- `ADMIN_IDS`: شناسه عددی مدیران، جداشده با کاما
- `DATABASE_URL`: مقدار PostgreSQL Railway؛ برنامه خودکار آن را به `postgresql+asyncpg://` تبدیل می‌کند
- `CARD_NUMBER`: شماره کارت دریافت وجه
- `CARD_OWNER`: نام صاحب کارت
- `SUPPORT_CONTACT`: آیدی پشتیبانی؛ `@Parham88e`
- `LOG_LEVEL`: معمولاً `INFO`
- `INSTANCE_LOCK_KEY`: عدد ثابت برای قفل polling؛ مقدار پیش‌فرض `1377642930` را تغییر ندهید مگر اینکه چند ربات مستقل از یک دیتابیس استفاده کنند

### اتصال PostgreSQL در Railway

1. در همان Railway Project گزینه **Add Service → Database → PostgreSQL** را انتخاب کنید.
2. سرویس Bot را باز کنید و در **Variables**، متغیر `DATABASE_URL` را به مقدار اتصال PostgreSQL متصل کنید؛ در Railway معمولاً با reference variable مانند `${{Postgres.DATABASE_URL}}` انجام می‌شود.
3. متغیرهای ربات را نیز در همان سرویس Bot وارد کنید.
4. فقط یک replica/instance برای Bot نگه دارید.
5. Deploy را انجام دهید و Logs را برای پیام `Virex bot is starting in polling mode` بررسی کنید.

SQLite فقط برای توسعه محلی مناسب است و روی filesystem موقت Railway توصیه نمی‌شود.

## دستورات مدیر

- `/admin` گزارش فروش و موجودی
- `/products`، `/addproduct نام حجم مدت قیمت`، `/editproduct شناسه حجم مدت قیمت`
- `/toggleproduct شناسه`، `/deleteproduct شناسه`
- `/addconfig شناس��_محصول متن_کانفیگ`، `/configs`، `/deleteconfig شناسه`
- `/confirm شناسه_داخلی` و `/reject شناسه_داخلی`
- `/walletadd شناسه_تلگرام مبلغ`
- `/user شناسه_تلگرام`، `/block شناسه_تلگرام`، `/unblock شناسه_تلگرام`

Virex بدون سیستم کد تخفیف فعالیت می‌کند. محصولات پیش‌فرض: 5GB/30,000، 10GB/60,000، 20GB/120,000، 50GB/200,000 و 100GB/345,000 تومان؛ همه ۳۰ روزه هستند.

# Virex

ربات فارسی فروش VPN با محصولات، موجودی کانفیگ، پرداخت کارت‌به‌کارت، کد تخفیف، کیف پول و تحویل امن پس از تأیید مدیر.

## اجرا
```bash
pip install -r requirements.txt
cp .env.example .env
python main.py
```

## دستورات مدیریت
پس از تنظیم `ADMIN_IDS`، مدیر با `/admin` گزارش را می‌بیند. دستورات اصلی: `/addproduct`، `/addconfig`، `/products`، `/user`، `/block`، `/unblock`، `/coupon` و `/broadcast`.

## تنظیمات
`BOT_TOKEN`، `ADMIN_IDS`، `DATABASE_URL`، `CARD_NUMBER`، `CARD_OWNER` و `SUPPORT_CONTACT` را در Railway Variables تنظیم کنید. اطلاعات حساس در Git ذخیره نمی‌شود. SQLite و PostgreSQL با `DATABASE_URL` پشتیبانی می‌شوند.

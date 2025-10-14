#!/bin/bash

# فایل به‌روزرسانی Docker برای دیباگ مشکل دکمه اضافه کردن

echo "🔄 Stopping Docker containers..."
docker compose down

echo "🧹 Removing old images..."
docker compose build --no-cache

echo "🚀 Starting Docker containers..."
docker compose up -d

echo "📊 Showing logs..."
docker compose logs -f
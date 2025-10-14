#!/bin/bash

echo "🔄 Updating PhoneBook Docker Application..."
echo "================================================"

# مرحله 1: متوقف کردن کانتینرها
echo "📦 Stopping containers..."
docker compose down

# مرحله 2: حذف تصاویر قدیمی
echo "🗑️ Removing old images..."
docker compose build --no-cache phonebook-app

# مرحله 3: راه‌اندازی مجدد
echo "🚀 Starting containers..."
docker compose up -d

# مرحله 4: نمایش وضعیت
echo "📊 Container status:"
docker compose ps

# مرحله 5: نمایش لاگ‌ها
echo "📋 Recent logs:"
docker compose logs phonebook-app --tail=20

echo "================================================"
echo "✅ Update completed!"
echo "🌐 Test URLs:"
echo "   - Main: http://phonebook.aftabnetad.com/"
echo "   - Version check: http://phonebook.aftabnetad.com/version"  
echo "   - Test page: http://phonebook.aftabnetad.com/test"
echo "   - Debug: http://phonebook.aftabnetad.com/debug/permissions"
echo ""
echo "💡 To follow logs: docker compose logs -f phonebook-app"
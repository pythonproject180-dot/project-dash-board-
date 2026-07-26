#!/bin/bash
# Hamro Hospital Management System - Setup Script
# Run this in GitHub Codespaces or locally after cloning

echo "🏥 Hamro Hospital Management System - Setup"
echo "============================================"

# Step 1: Install dependencies
echo "📦 Step 1: Installing dependencies..."
pip install -r requirements.txt

# Step 2: Run migrations
echo "🗄️ Step 2: Running database migrations..."
python manage.py migrate

# Step 3: Seed base data (14 staff accounts, provinces, departments, doctors, services, etc.)
echo "🌱 Step 3: Seeding base data..."
python manage.py seed_all

# Step 4: Expand seed data (100 medicines, 10+ items per category)
echo "📊 Step 4: Expanding seed data..."
python manage.py seed_expand

# Step 5: Start server
echo "🚀 Step 5: Starting server on port 8000..."
echo ""
echo "============================================"
echo "✅ SETUP COMPLETE!"
echo ""
echo "📍 Access URLs:"
echo "   Public Website:  http://localhost:8000/"
echo "   Staff Login:     http://localhost:8000/accounts/login/"
echo "   Django Admin:    http://localhost:8000/admin/"
echo "   Patient Portal:  http://localhost:8000/portal/signup/"
echo ""
echo "🔐 Staff Accounts (all use password: password123*#):"
echo "   admin, registration, cashier, doctor, pharmacy, laboratory,"
echo "   radiology, insurance, admission, nursing, operationtheatre,"
echo "   bloodbank, accounts, medicalrecords"
echo ""
echo "🚀 Starting server now..."
python manage.py runserver 0.0.0.0:8000

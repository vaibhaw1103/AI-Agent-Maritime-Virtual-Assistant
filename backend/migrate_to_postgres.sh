#!/bin/bash

# Maritime Assistant - PostgreSQL Migration Script
# This script helps migrate from SQLite to PostgreSQL

echo "🚢 Maritime Assistant - Database Migration"
echo "==========================================="

# Check if PostgreSQL is running
echo "📡 Checking PostgreSQL service..."

# For Windows (using sc command)
if command -v sc &> /dev/null; then
    PG_STATUS=$(sc query postgresql-x64-16 2>/dev/null | grep STATE | awk '{print $4}')
    if [ "$PG_STATUS" != "RUNNING" ]; then
        echo "⚠️  PostgreSQL service not running. Starting..."
        echo "Please start PostgreSQL service manually or run:"
        echo "   net start postgresql-x64-16"
        exit 1
    fi
fi

echo "✅ PostgreSQL is running"

# Step 1: Create database and user
echo "🗄️  Step 1: Setting up PostgreSQL database..."
python setup_postgres.py

if [ $? -eq 0 ]; then
    echo "✅ Database setup completed"
else
    echo "❌ Database setup failed"
    exit 1
fi

# Step 2: Update environment file
echo "📝 Step 2: Updating environment configuration..."
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
fi

# Update DATABASE_URL in .env
if grep -q "DATABASE_URL=" .env; then
    # Update existing line
    sed -i 's|DATABASE_URL=.*|DATABASE_URL=postgresql://maritime_user:maritime_pass@localhost:5432/maritime_assistant_db|' .env
else
    # Add new line
    echo "DATABASE_URL=postgresql://maritime_user:maritime_pass@localhost:5432/maritime_assistant_db" >> .env
fi

echo "✅ Environment configuration updated"

# Step 3: Create initial migration
echo "🔄 Step 3: Creating database migration..."
python -m alembic revision --autogenerate -m "Initial maritime assistant schema"

if [ $? -eq 0 ]; then
    echo "✅ Migration created successfully"
else
    echo "❌ Migration creation failed"
    exit 1
fi

# Step 4: Run migration
echo "⬆️  Step 4: Applying database migration..."
python -m alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migration applied successfully"
else
    echo "❌ Migration failed"
    exit 1
fi

# Step 5: Test the connection
echo "🧪 Step 5: Testing database connection..."
python -c "
from database import engine, SessionLocal
try:
    with engine.connect() as conn:
        result = conn.execute('SELECT 1').fetchone()
        print('✅ Database connection successful!')
    
    # Test session
    session = SessionLocal()
    session.close()
    print('✅ Database sessions working correctly!')
    
except Exception as e:
    print(f'❌ Connection test failed: {e}')
    exit(1)
"

echo ""
echo "🎉 PostgreSQL migration completed successfully!"
echo ""
echo "📋 Summary:"
echo "   • PostgreSQL database: maritime_assistant_db"
echo "   • Database user: maritime_user"
echo "   • Connection: postgresql://maritime_user:maritime_pass@localhost:5432/maritime_assistant_db"
echo ""
echo "🚀 Next steps:"
echo "   1. Start your backend: python main.py"
echo "   2. Test the application: http://localhost:8000"
echo "   3. Check database status: http://localhost:8000/settings"

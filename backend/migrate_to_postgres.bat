@echo off
REM Maritime Assistant - PostgreSQL Migration Script (Windows)
REM This script helps migrate from SQLite to PostgreSQL on Windows

echo 🚢 Maritime Assistant - Database Migration
echo ===========================================

REM Check if PostgreSQL is running
echo 📡 Checking PostgreSQL service...
sc query postgresql-x64-16 | find "RUNNING" >nul
if %errorlevel% neq 0 (
    echo ⚠️  PostgreSQL service not running. 
    echo Please start PostgreSQL service:
    echo    Services.msc or run: net start postgresql-x64-16
    pause
    exit /b 1
)

echo ✅ PostgreSQL is running

REM Step 1: Create database and user
echo 🗄️  Step 1: Setting up PostgreSQL database...
python setup_postgres.py

if %errorlevel% neq 0 (
    echo ❌ Database setup failed
    pause
    exit /b 1
)

echo ✅ Database setup completed

REM Step 2: Update environment file
echo 📝 Step 2: Updating environment configuration...
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
)

REM Update DATABASE_URL in .env (simple approach for Windows)
echo DATABASE_URL=postgresql://maritime_user:maritime_pass@localhost:5432/maritime_assistant_db > temp_env.txt
findstr /v "DATABASE_URL=" .env >> temp_env.txt
move temp_env.txt .env

echo ✅ Environment configuration updated

REM Step 3: Create initial migration
echo 🔄 Step 3: Creating database migration...
python -m alembic revision --autogenerate -m "Initial maritime assistant schema"

if %errorlevel% neq 0 (
    echo ❌ Migration creation failed
    pause
    exit /b 1
)

echo ✅ Migration created successfully

REM Step 4: Run migration
echo ⬆️  Step 4: Applying database migration...
python -m alembic upgrade head

if %errorlevel% neq 0 (
    echo ❌ Migration failed
    pause
    exit /b 1
)

echo ✅ Migration applied successfully

REM Step 5: Test the connection
echo 🧪 Step 5: Testing database connection...
python -c "from database import engine, SessionLocal; import sys; exec('try:\n    with engine.connect() as conn:\n        result = conn.execute(\"SELECT 1\").fetchone()\n        print(\"✅ Database connection successful!\")\n    session = SessionLocal()\n    session.close()\n    print(\"✅ Database sessions working correctly!\")\nexcept Exception as e:\n    print(f\"❌ Connection test failed: {e}\")\n    sys.exit(1)')"

if %errorlevel% neq 0 (
    pause
    exit /b 1
)

echo.
echo 🎉 PostgreSQL migration completed successfully!
echo.
echo 📋 Summary:
echo    • PostgreSQL database: maritime_assistant_db
echo    • Database user: maritime_user
echo    • Connection: postgresql://maritime_user:maritime_pass@localhost:5432/maritime_assistant_db
echo.
echo 🚀 Next steps:
echo    1. Start your backend: python main.py
echo    2. Test the application: http://localhost:8000
echo    3. Check database status: http://localhost:8000/settings

pause

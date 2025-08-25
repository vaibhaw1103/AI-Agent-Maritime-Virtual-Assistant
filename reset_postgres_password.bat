@echo off
echo Stopping PostgreSQL service...
net stop postgresql-x64-17

echo Starting PostgreSQL in single-user mode (no authentication)...
echo Please wait for the service to start in recovery mode...

echo.
echo To reset password, run these commands:
echo.
echo 1. Open another command prompt as Administrator
echo 2. Run: psql -U postgres
echo 3. In psql, run: ALTER USER postgres PASSWORD 'newpassword';
echo 4. Type \q to quit
echo 5. Come back here and press any key to restart normal service

pause

echo Starting PostgreSQL service normally...
net start postgresql-x64-17
echo PostgreSQL password has been reset!

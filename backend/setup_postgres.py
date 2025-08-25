"""
Maritime Assistant Database Initialization Script
Creates PostgreSQL database and user for the maritime assistant application.
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database():
    """Create PostgreSQL database and user for maritime assistant."""
    
    # Database configuration
    DB_NAME = "maritime_assistant_db"
    DB_USER = "maritime_user"  
    DB_PASS = "maritime_pass"
    DB_HOST = "localhost"
    DB_PORT = "5432"
    
    print("🚢 Maritime Assistant - PostgreSQL Setup")
    print("=" * 50)
    
    try:
        # Connect to PostgreSQL server (default database)
        print("📡 Connecting to PostgreSQL server...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user="postgres",  # Default postgres user
            password=input("Enter PostgreSQL admin password: ")
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create user
        print(f"👤 Creating database user: {DB_USER}")
        try:
            cursor.execute(f"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASS}';")
            print("✅ Database user created successfully")
        except psycopg2.errors.DuplicateObject:
            print("⚠️  User already exists, skipping...")
        
        # Create database
        print(f"🗄️  Creating database: {DB_NAME}")
        try:
            cursor.execute(f"CREATE DATABASE {DB_NAME} OWNER {DB_USER};")
            print("✅ Database created successfully")
        except psycopg2.errors.DuplicateDatabase:
            print("⚠️  Database already exists, skipping...")
        
        # Grant privileges
        print("🔐 Granting database privileges...")
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};")
        cursor.execute(f"ALTER USER {DB_USER} CREATEDB;")  # For running tests
        
        print("✅ PostgreSQL setup completed successfully!")
        print("\n📋 Database Configuration:")
        print(f"   Database: {DB_NAME}")
        print(f"   User: {DB_USER}")
        print(f"   Host: {DB_HOST}:{DB_PORT}")
        print(f"\n🔗 Connection String:")
        print(f"   DATABASE_URL=postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
        
        # Close connections
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL Error: {e}")
        print("\n🛠️  Troubleshooting:")
        print("   1. Ensure PostgreSQL is installed and running")
        print("   2. Check PostgreSQL admin password")
        print("   3. Verify PostgreSQL is accessible on localhost:5432")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_connection():
    """Test connection to the newly created database."""
    try:
        print("\n🧪 Testing database connection...")
        conn = psycopg2.connect(
            host="localhost",
            port="5432", 
            database="maritime_assistant_db",
            user="maritime_user",
            password="maritime_pass"
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Connection successful!")
        print(f"   PostgreSQL Version: {version}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚢 Maritime Assistant - PostgreSQL Database Setup")
    print("This script will create the PostgreSQL database and user.")
    print("\n📋 Prerequisites:")
    print("   • PostgreSQL installed and running")  
    print("   • PostgreSQL admin (postgres) password")
    
    proceed = input("\nProceed with database setup? (y/N): ").lower()
    if proceed in ['y', 'yes']:
        if create_database():
            test_connection()
            print("\n🎉 Setup complete! Update your .env file with:")
            print("DATABASE_URL=postgresql://maritime_user:maritime_pass@localhost:5432/maritime_assistant_db")
        else:
            print("\n❌ Setup failed. Please check the errors above.")
    else:
        print("Setup cancelled.")

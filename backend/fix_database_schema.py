#!/usr/bin/env python3
"""
Fix database schema for smart ports
"""

import sqlite3
import os

def fix_database_schema():
    """Fix the database schema to support smart ports"""
    
    print('🔧 Fixing database schema for smart ports...')
    
    db_file = 'ports.db'
    if not os.path.exists(db_file):
        print('❌ Database not found')
        return False
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute('PRAGMA table_info(ports)')
        columns = cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        
        print(f'📋 Current columns: {existing_columns}')
        
        # Add missing columns
        added_columns = []
        
        if 'size_category' not in existing_columns:
            cursor.execute('ALTER TABLE ports ADD COLUMN size_category TEXT DEFAULT "Medium"')
            added_columns.append('size_category')
            print('✅ Added size_category column')
        
        if 'created_source' not in existing_columns:
            cursor.execute('ALTER TABLE ports ADD COLUMN created_source TEXT DEFAULT "Manual"')
            added_columns.append('created_source')
            print('✅ Added created_source column')
        
        # Also ensure harbor_size exists (some queries use this)
        if 'harbor_size' not in existing_columns:
            cursor.execute('ALTER TABLE ports ADD COLUMN harbor_size TEXT DEFAULT "Medium"')
            added_columns.append('harbor_size')
            print('✅ Added harbor_size column')
        
        conn.commit()
        conn.close()
        
        if added_columns:
            print(f'✅ Database schema updated! Added: {", ".join(added_columns)}')
        else:
            print('✅ Database schema already up to date')
        
        return True
        
    except Exception as e:
        print(f'❌ Error updating schema: {e}')
        return False

if __name__ == "__main__":
    success = fix_database_schema()
    if success:
        print('🎯 Database is now ready for smart ports!')
    else:
        print('❌ Failed to update database schema')

#!/usr/bin/env python3
"""
Database Migration Script
Adds V2 columns to existing vendors table
Safe to run multiple times (checks if columns exist)
"""

import sqlite3
import os

VENDORS_DB = "data/vendors.db"

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def migrate_database():
    """Add missing V2 columns to vendors table"""
    
    if not os.path.exists(VENDORS_DB):
        print(f"❌ Database not found: {VENDORS_DB}")
        return
    
    conn = sqlite3.connect(VENDORS_DB)
    cursor = conn.cursor()
    
    # List of new columns to add for V2 features
    new_columns = [
        ("discovered_date", "TEXT"),
        ("contact_email", "TEXT"),
        ("product_description", "TEXT"),
        ("keywords_used", "TEXT"),
        ("validation_status", "TEXT"),
        ("rejection_reason", "TEXT"),
        ("email_sent_count", "INTEGER DEFAULT 0"),
        ("last_email_date", "TEXT"),
        ("email_response", "TEXT"),
        ("price_quoted", "REAL"),
        ("moq_quoted", "INTEGER"),
        ("customization_confirmed", "TEXT"),
        ("response_time_hours", "REAL"),
        ("last_response_date", "TEXT"),
    ]
    
    print("🔄 Starting database migration...")
    print(f"Database: {VENDORS_DB}")
    print("-" * 60)
    
    added_count = 0
    skipped_count = 0
    
    for column_name, column_type in new_columns:
        if column_exists(cursor, "vendors", column_name):
            print(f"⏭️  Column '{column_name}' already exists - skipping")
            skipped_count += 1
        else:
            try:
                cursor.execute(f"ALTER TABLE vendors ADD COLUMN {column_name} {column_type}")
                print(f"✅ Added column: {column_name} ({column_type})")
                added_count += 1
            except sqlite3.OperationalError as e:
                print(f"⚠️  Error adding column '{column_name}': {e}")
    
    conn.commit()
    conn.close()
    
    print("-" * 60)
    print(f"✅ Migration complete!")
    print(f"   - Columns added: {added_count}")
    print(f"   - Columns skipped: {skipped_count}")
    print(f"   - Total V2 columns: {len(new_columns)}")
    
    # Verify the schema
    conn = sqlite3.connect(VENDORS_DB)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(vendors)")
    columns = cursor.fetchall()
    conn.close()
    
    print(f"\n📊 Current schema has {len(columns)} columns total")
    print("\nNew V2 columns verified:")
    for col_name, col_type in new_columns:
        exists = "✓" if any(col[1] == col_name for col in columns) else "✗"
        print(f"   {exists} {col_name}")

if __name__ == "__main__":
    migrate_database()

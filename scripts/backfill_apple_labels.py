#!/usr/bin/env python3.11
"""Pictovap - Apple ML Labels Backfill Script
This script populates the newly added `apple_labels_json` column 
for all existing photos in the database by reading from osxphotos.
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
import osxphotos

DB_PATH = Path(os.environ.get(
    "YO_VISUAL_MEMORY_DB",
    "/Users/yoldaolmak/Projects/Pictovap/data/visual_memory.db",
))

def main():
    print("📸 Loading Photos Library...")
    db_photos = osxphotos.PhotosDB()
    
    print("📦 Connecting to database...")
    con = sqlite3.connect(str(DB_PATH))
    
    # Get all source_ids that don't have apple_labels_json populated
    # (Or just all of them to be safe)
    rows = con.execute("SELECT source_id FROM asset_index").fetchall()
    
    print(f"🔍 Found {len(rows):,} photos in database. Starting backfill...")
    
    updated = 0
    errors = 0
    
    # We will use executemany for faster updates in batches
    batch_size = 1000
    batch_data = []
    
    for row in rows:
        uuid = row[0]
        try:
            photo = db_photos.get_photo(uuid)
            if photo:
                labels = getattr(photo, "labels", None) or []
                labels_json = json.dumps(labels, ensure_ascii=False)
                batch_data.append((labels_json, uuid))
                updated += 1
        except Exception as e:
            errors += 1
            pass
            
        if len(batch_data) >= batch_size:
            con.executemany("UPDATE asset_index SET apple_labels_json = ? WHERE source_id = ?", batch_data)
            con.commit()
            print(f"   Processed {updated:,} photos...")
            batch_data = []
            
    # Process remaining
    if batch_data:
        con.executemany("UPDATE asset_index SET apple_labels_json = ? WHERE source_id = ?", batch_data)
        con.commit()
        
    con.close()
    
    print("\n✅ Backfill Complete")
    print(f"   Updated: {updated:,}")
    print(f"   Errors: {errors:,}")

if __name__ == "__main__":
    main()

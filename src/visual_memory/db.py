"""
Visual Memory Database - Legacy compatibility module

This module provides backward-compatible interface for visual memory database operations.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any


class VisualMemoryDatabase:
    """
    Legacy database interface for visual memory
    
    Maintains compatibility with existing code while providing
    core database functionality.
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
    
    @property
    def connection(self) -> sqlite3.Connection:
        """Get or create database connection"""
        if self._conn is None:
            if not self.db_path.exists():
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL query"""
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor
    
    def commit(self):
        """Commit current transaction"""
        self.connection.commit()
    
    def close(self):
        """Close database connection"""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def get_all_images(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all images from database"""
        cursor = self.execute("""
            SELECT * FROM images
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_image_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Get image by path"""
        cursor = self.execute("""
            SELECT * FROM images WHERE path = ?
        """, (path,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_tags_for_image(self, image_id: int) -> List[str]:
        """Get all tags for an image"""
        cursor = self.execute("""
            SELECT tag FROM tags WHERE image_id = ?
            ORDER BY confidence DESC
        """, (image_id,))
        return [row['tag'] for row in cursor.fetchall()]

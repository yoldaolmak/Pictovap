"""
Visual Memory Database - Legacy compatibility module

This module provides backward-compatible interface for visual memory database operations.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class VisualMemoryConfig:
    """Configuration for VisualMemoryComponent"""
    database_path: Path
    external_roots: List[Path] = None
    scan_photos_library: bool = False
    
    def __post_init__(self):
        if self.external_roots is None:
            self.external_roots = []


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


class VisualMemoryComponent:
    """
    Component for managing visual memory assets.
    Provides list_assets and other operations for asset selection.
    """
    
    def __init__(self, config: VisualMemoryConfig):
        self.config = config
        self.db = VisualMemoryDatabase(config.database_path)
    
    def list_assets(
        self,
        limit: int = 20,
        source_root: Path = None,
        filename_query: str = None,
        source_types: tuple = None,
    ) -> List[Dict[str, Any]]:
        """
        List assets from the visual memory database.
        
        Args:
            limit: Maximum number of results
            source_root: Filter by source root path
            filename_query: Filter by filename (partial match)
            source_types: Filter by source types (e.g., ('external_hdd',))
        
        Returns:
            List of asset dictionaries with keys: source_path, filename, etc.
        """
        if not self.config.database_path.exists():
            return []
        
        conditions = ["is_personal = 0"]
        params = []
        
        if source_root:
            conditions.append("source_path LIKE ?")
            params.append(f"{source_root}%")
        
        if filename_query:
            conditions.append("filename LIKE ?")
            params.append(f"%{filename_query}%")
        
        if source_types:
            placeholders = ",".join("?" * len(source_types))
            conditions.append(f"source_type IN ({placeholders})")
            params.extend(source_types)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT source_path, filename, quality_score, selection_score,
                   activity, scene, location, orientation, title, description,
                   summary
            FROM asset_index
            WHERE {where_clause}
            ORDER BY selection_score DESC, quality_score DESC
            LIMIT ?
        """
        params.append(limit)
        
        try:
            cursor = self.db.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                asset = {key: row[key] for key in row.keys()}
                result.append(asset)
            
            return result
        finally:
            self.db.close()
    
    def get_all_images(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all images from database"""
        cursor = self.db.execute("""
            SELECT * FROM images
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_image_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Get image by path"""
        cursor = self.db.execute("""
            SELECT * FROM images WHERE path = ?
        """, (path,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_tags_for_image(self, image_id: int) -> List[str]:
        """Get all tags for an image"""
        cursor = self.db.execute("""
            SELECT tag FROM tags WHERE image_id = ?
            ORDER BY confidence DESC
        """, (image_id,))
        return [row['tag'] for row in cursor.fetchall()]

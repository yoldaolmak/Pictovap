"""
Visual Memory Component - Core module for image indexing and retrieval

This module provides the main interface for storing and querying image metadata,
tags, and semantic information in the visual memory database.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class VisualMemoryConfig:
    """Configuration for Visual Memory component"""
    db_path: Path
    auto_create: bool = True
    cache_enabled: bool = True


class VisualMemoryComponent:
    """
    Main component for managing visual memory database
    
    Handles image indexing, tag storage, and semantic search capabilities
    """
    
    def __init__(self, config: VisualMemoryConfig):
        self.config = config
        self.db_path = config.db_path
        self._conn: Optional[sqlite3.Connection] = None
    
    @property
    def connection(self) -> sqlite3.Connection:
        """Get or create database connection"""
        if self._conn is None:
            if not self.db_path.exists() and self.config.auto_create:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._init_schema()
        return self._conn
    
    def _init_schema(self):
        """Initialize database schema if not exists"""
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                width INTEGER,
                height INTEGER,
                file_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                tag TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT 'manual',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES images(id),
                UNIQUE(image_id, tag)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS semantic_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                embedding BLOB,
                model TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES images(id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tags_image ON tags(image_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag)
        """)
        
        self.connection.commit()
    
    def add_image(self, path: Path, width: Optional[int] = None, 
                  height: Optional[int] = None, file_size: Optional[int] = None) -> int:
        """Add or update image record"""
        cursor = self.connection.cursor()
        filename = path.name
        
        try:
            cursor.execute("""
                INSERT INTO images (path, filename, width, height, file_size)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    filename = excluded.filename,
                    width = COALESCE(excluded.width, images.width),
                    height = COALESCE(excluded.height, images.height),
                    file_size = COALESCE(excluded.file_size, images.file_size),
                    updated_at = CURRENT_TIMESTAMP
            """, (str(path), filename, width, height, file_size))
            self.connection.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            cursor.execute("SELECT id FROM images WHERE path = ?", (str(path),))
            row = cursor.fetchone()
            return row[0] if row else -1
    
    def add_tag(self, image_id: int, tag: str, confidence: float = 1.0, 
                source: str = 'manual') -> bool:
        """Add tag to an image"""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO tags (image_id, tag, confidence, source)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(image_id, tag) DO UPDATE SET
                    confidence = excluded.confidence,
                    source = excluded.source
            """, (image_id, tag, confidence, source))
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_images_by_tag(self, tag: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all images with a specific tag"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT i.* FROM images i
            JOIN tags t ON i.id = t.image_id
            WHERE t.tag = ?
            ORDER BY t.confidence DESC, i.created_at DESC
            LIMIT ?
        """, (tag, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def search_images(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search images by tag or filename"""
        cursor = self.connection.cursor()
        search_pattern = f"%{query}%"
        
        cursor.execute("""
            SELECT DISTINCT i.* FROM images i
            LEFT JOIN tags t ON i.id = t.image_id
            WHERE i.filename LIKE ? OR t.tag LIKE ?
            ORDER BY i.created_at DESC
            LIMIT ?
        """, (search_pattern, search_pattern, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection"""
        if self._conn:
            self._conn.close()
            self._conn = None


def load_visual_memory(db_path: Optional[Path] = None) -> VisualMemoryComponent:
    """Load visual memory component with default or custom path"""
    if db_path is None:
        from src.core.settings import get_visual_memory_db_path
        db_path = get_visual_memory_db_path()
    
    config = VisualMemoryConfig(db_path=db_path)
    return VisualMemoryComponent(config)

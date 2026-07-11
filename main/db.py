import sqlite3
import time
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

from main.constants import DB_FILE
from main.models import WorkMetadata

class LibraryVault:
    """Manages download history and library database."""
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS works (
                    rj_id TEXT PRIMARY KEY,
                    title TEXT,
                    circle TEXT,
                    downloaded_at TIMESTAMP,
                    size_bytes INTEGER DEFAULT 0,
                    local_path TEXT
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS download_queue (
                    rj_id TEXT PRIMARY KEY,
                    priority INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    added_at TIMESTAMP
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS file_states (
                    rj_id TEXT,
                    file_path TEXT,
                    total_size INTEGER,
                    downloaded_size INTEGER,
                    status TEXT,
                    PRIMARY KEY (rj_id, file_path)
                )
            """)
            # Migration: add missing columns
            try:
                self.conn.execute("ALTER TABLE works ADD COLUMN size_bytes INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass  # Column already exists
                
            try:
                self.conn.execute("ALTER TABLE works ADD COLUMN local_path TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                self.conn.execute("ALTER TABLE works ADD COLUMN cover_url TEXT DEFAULT ''")
            except sqlite3.OperationalError:
                pass  # Column already exists

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def register(self, meta: WorkMetadata, size: int, path: Path) -> None:
        """Register a downloaded work in the database."""
        with self.conn:
            self.conn.execute(
                """INSERT OR REPLACE INTO works 
                   (rj_id, title, circle, downloaded_at, size_bytes, local_path, cover_url) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (meta.rj_id, meta.title, meta.circle, datetime.now(), size, str(path), getattr(meta, 'cover_url', ''))
            )
        self._summary_cache_time = 0  # invalidate cache so draw_header() reflects new work

    def get_work(self, rj_id: str) -> Optional[sqlite3.Row]:
        """Get a work from the library by RJ code."""
        return self.conn.execute("SELECT * FROM works WHERE rj_id = ?", (rj_id,)).fetchone()

    def get_summary(self) -> Tuple[int, int]:
        """Get total works and total library size."""
        if hasattr(self, '_summary_cache_time') and time.time() - self._summary_cache_time < 30:
            return self._summary_cache
            
        row = self.conn.execute("SELECT COUNT(*), SUM(size_bytes) FROM works").fetchone()
        self._summary_cache = (row[0] or 0, row[1] or 0)
        self._summary_cache_time = time.time()
        return self._summary_cache

    def search(self, query: str = "") -> List[sqlite3.Row]:
        """Search for works in the library."""
        if not query:
            sql = "SELECT * FROM works ORDER BY downloaded_at DESC LIMIT 50"
            return self.conn.execute(sql).fetchall()
        
        q = f"%{query}%"
        sql = """SELECT * FROM works 
                 WHERE title LIKE ? OR rj_id LIKE ? OR circle LIKE ? 
                 ORDER BY downloaded_at DESC LIMIT 50"""
        return self.conn.execute(sql, (q, q, q)).fetchall()

    def queue_add(self, rj_id: str, priority: int = 0) -> None:
        """Add an RJ code to the download queue."""
        with self.conn:
            self.conn.execute(
                """INSERT OR REPLACE INTO download_queue 
                   (rj_id, priority, status, added_at) 
                   VALUES (?, ?, 'pending', ?)""",
                (rj_id, priority, datetime.now())
            )

    def queue_remove(self, rj_id: str) -> None:
        """Remove an RJ code from the download queue."""
        with self.conn:
            self.conn.execute("DELETE FROM download_queue WHERE rj_id = ?", (rj_id,))

    def repair_database(self) -> Tuple[bool, str]:
        """Run PRAGMA integrity_check and VACUUM."""
        try:
            with self.conn:
                cursor = self.conn.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                if result and str(result[0]).lower() != "ok":
                    return False, f"Integrity check failed: {result[0]}"
                self.conn.execute("VACUUM")
            return True, "Database repaired and optimized successfully."
        except Exception as e:
            return False, str(e)

    def queue_update_status(self, rj_id: str, status: str) -> None:
        """Update status of a queue item (pending, active, paused, completed)."""
        with self.conn:
            self.conn.execute("UPDATE download_queue SET status = ? WHERE rj_id = ?", (status, rj_id))

    def queue_update_priority(self, rj_id: str, priority: int) -> None:
        """Update priority of a queue item."""
        with self.conn:
            self.conn.execute("UPDATE download_queue SET priority = ? WHERE rj_id = ?", (priority, rj_id))

    def queue_get_all(self) -> List[sqlite3.Row]:
        """Get all queued items."""
        return self.conn.execute("SELECT * FROM download_queue ORDER BY priority DESC, added_at ASC").fetchall()

    def queue_get_pending(self) -> List[sqlite3.Row]:
        """Get pending items ordered by priority."""
        return self.conn.execute("SELECT * FROM download_queue WHERE status = 'pending' ORDER BY priority DESC, added_at ASC").fetchall()

    def queue_clear(self) -> None:
        """Remove all items from the download queue."""
        with self.conn:
            self.conn.execute("DELETE FROM download_queue")

    def file_state_update(self, rj_id: str, file_path: str, total_size: int, downloaded_size: int, status: str) -> None:
        """Update the checkpoint state of a specific file."""
        with self.conn:
            self.conn.execute(
                """INSERT OR REPLACE INTO file_states 
                   (rj_id, file_path, total_size, downloaded_size, status) 
                   VALUES (?, ?, ?, ?, ?)""",
                (rj_id, file_path, total_size, downloaded_size, status)
            )

    def file_state_get(self, rj_id: str, file_path: str) -> Optional[sqlite3.Row]:
        """Get the checkpoint state of a specific file."""
        return self.conn.execute(
            "SELECT * FROM file_states WHERE rj_id = ? AND file_path = ?", 
            (rj_id, file_path)
        ).fetchone()

    def export_library(self, path: Path) -> bool:
        """Export the library to a CSV or JSON file based on the extension."""
        try:
            works = self.conn.execute("SELECT * FROM works ORDER BY downloaded_at DESC").fetchall()
            data = [dict(w) for w in works]
            
            ext = path.suffix.lower()
            if ext == '.json':
                import json
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif ext == '.csv':
                import csv
                if not data:
                    with open(path, 'w', encoding='utf-8') as f:
                        pass
                    return True
                keys = data[0].keys()
                with open(path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(data)
            else:
                return False
            return True
        except Exception:
            import logging
            logging.exception("Failed to export library")
            return False


#!/usr/bin/env python
# encoding: utf-8

"""
progress_manager.py

Handles database operations for tracking book progress.
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)

class ProgressManager:
    """Handles database operations for tracking book progress."""

    def __init__(self, db_file: str):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)
        self._init_db()

    def _init_db(self):
        create_table_query = """
            CREATE TABLE IF NOT EXISTS progress (
                book_id BIGINT NOT NULL PRIMARY KEY,
                elapsed REAL NOT NULL,
                part INTEGER NOT NULL
            );
        """
        with self.conn:
            self.conn.execute(create_table_query)

    def get_progress(self, book_id: int):
        query = "SELECT * FROM progress WHERE book_id = ?"
        cursor = self.conn.execute(query, (book_id,))
        return cursor.fetchone()

    def update_progress(self, book_id: int, part: int, elapsed: float):
        book_id = int(book_id)
        part = int(part)
        elapsed = float(elapsed)

        query = """
            INSERT OR REPLACE INTO progress (book_id, part, elapsed)
            VALUES (?, ?, ?)
        """
        with self.conn:
            self.conn.execute(query, (book_id, part, elapsed))

    def delete_progress(self, book_id: int):
        query = "DELETE FROM progress WHERE book_id = ?"
        with self.conn:
            self.conn.execute(query, (book_id,))

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    import os
    import sys

    # Use state.db in the current directory as default
    db_file = os.path.join(os.path.dirname(__file__), "state.db")

    if not os.path.exists(db_file):
        print(f"Database file {db_file} does not exist")
        sys.exit(1)

    pm = ProgressManager(db_file)
    
    try:
        # Query all records from progress table
        with pm.conn:
            cursor = pm.conn.execute("SELECT book_id, elapsed, part FROM progress")
            rows = cursor.fetchall()
            
        if not rows:
            print("No progress records found in database")
        else:
            print("\nCurrent progress records:")
            print("-" * 50)
            print(f"{'Book ID':>10} | {'Part':>6} | {'Elapsed Time':>12}")
            print("-" * 50)
            for row in rows:
                book_id, elapsed, part = row
                print(f"{book_id:>10} | {part:>6} | {elapsed:>12.2f}")
            print("-" * 50)
            
    finally:
        pm.close()

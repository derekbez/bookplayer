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
    """
    Handles database operations for tracking book progress.
    Each book's progress (book_id, part, elapsed) is stored in a SQLite table.
    """
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)
        self._init_db()

    def _init_db(self):
        """
        Create the progress table if it does not exist.
        """
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
        """
        Retrieve progress for a given book ID.
        Returns:
            tuple: (book_id, elapsed, part) or None if not found.
        """
        query = "SELECT * FROM progress WHERE book_id = ?"
        cursor = self.conn.execute(query, (book_id,))
        return cursor.fetchone()

    def update_progress(self, book_id: int, part: int, elapsed: float):
        """
        Insert or update progress for a book.
        Args:
            book_id (int): The book's unique ID.
            part (int): The current part/chapter.
            elapsed (float): Elapsed time in seconds.
        """
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
        """
        Delete progress record for a given book ID.
        """
        query = "DELETE FROM progress WHERE book_id = ?"
        with self.conn:
            self.conn.execute(query, (book_id,))

    def close(self):
        """
        Close the database connection.
        """
        self.conn.close()

if __name__ == "__main__":
    import os
    import sys
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Use state.db in the current directory as default
    db_file = os.path.join(os.path.dirname(__file__), "state.db")

    if not os.path.exists(db_file):
        logger.error(f"Database file {db_file} does not exist")
        sys.exit(1)

    pm = ProgressManager(db_file)
    try:
        # Query all records from progress table
        with pm.conn:
            cursor = pm.conn.execute("SELECT book_id, elapsed, part FROM progress")
            rows = cursor.fetchall()

        if not rows:
            logger.info("No progress records found in database")
        else:
            # Format the progress records table
            table_header = f"{'Book ID':>10} | {'Part':>6} | {'Elapsed Time':>12}"
            separator = "-" * 50

            logger.info("\nCurrent progress records:")
            logger.info(separator)
            logger.info(table_header)
            logger.info(separator)

            for row in rows:
                book_id, elapsed, part = row
                logger.info(f"{book_id:>10} | {part:>6} | {elapsed:>12.2f}")

            logger.info(separator)
    finally:
        pm.close()

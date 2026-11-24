"""Long-term memory in SQLite: remembered facts and notes."""
import sqlite3
from datetime import datetime
from config import DB_PATH


class Memory:
    def __init__(self, path=DB_PATH):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute("CREATE TABLE IF NOT EXISTS facts (key TEXT PRIMARY KEY, value TEXT)")
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, created TEXT)"
        )
        self.conn.commit()

    # facts
    def remember(self, key: str, value: str):
        self.conn.execute("INSERT OR REPLACE INTO facts VALUES (?, ?)", (key.lower().strip(), value))
        self.conn.commit()

    def recall(self, key: str):
        row = self.conn.execute("SELECT value FROM facts WHERE key = ?", (key.lower().strip(),)).fetchone()
        return row[0] if row else None

    def all_facts(self) -> dict:
        return dict(self.conn.execute("SELECT key, value FROM facts").fetchall())

    # notes
    def add_note(self, text: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO notes (text, created) VALUES (?, ?)", (text, datetime.now().isoformat(timespec="minutes"))
        )
        self.conn.commit()
        return cur.lastrowid

    def list_notes(self):
        return self.conn.execute("SELECT id, text, created FROM notes ORDER BY id DESC LIMIT 20").fetchall()

    def delete_note(self, note_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self.conn.commit()
        return cur.rowcount > 0


memory = Memory()
import collections
import json

import psycopg2
from psycopg2 import sql

import config


DEFAULT_NOTES = """
{
  "id": 0,
  "type": "notebook",
  "title": "Notes",
  "notes": [
    {
      "id": 1,
      "type": "note",
      "title": "My First Note",
      "content": "Hello, World!"
    }
  ]
}
"""


class Database:
    def __init__(self):
        self.create_db_if_not_exists()
        
        self.conn = psycopg2.connect(
            host=config.DB_SECRETS["host"],
            user=config.DB_SECRETS["user"],
            password=config.DB_SECRETS["password"],
            dbname="freenote_users"
        )
        
        self.create_table_if_not_exists()
        
    def __del__(self):
        if hasattr(self, "conn") and self.conn is not None:
            self.conn.close()
    
    @staticmethod
    def create_db_if_not_exists():
        conn = psycopg2.connect(
            host=config.DB_SECRETS["host"],
            user=config.DB_SECRETS["user"],
            password=config.DB_SECRETS["password"]
        )
        
        conn.autocommit = True
        
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier('freenote_users')))
        except psycopg2.errors.DuplicateDatabase:
            pass
        
        cursor.close()
        conn.close()
    
    def create_table_if_not_exists(self):
        cursor = self.conn.cursor()
        
        # Create the 'users' table inside the 'freenote_users' database
        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS users (
                                google_id TEXT PRIMARY KEY NOT NULL,
                                email TEXT NOT NULL,
                                notes_id_counter INT NOT NULL DEFAULT 2,
                                notes JSONB NOT NULL DEFAULT %s
                            )
                        """, (DEFAULT_NOTES,))
        
        self.conn.commit()
        cursor.close()
    
    def user_exists(self, google_id) -> bool:
        cursor = self.conn.cursor()
        
        cursor.execute("""
                            SELECT COUNT(*)
                            FROM users
                            WHERE google_id = %s
                        """, (google_id,))
        
        count = cursor.fetchone()[0]
        
        cursor.close()
        
        return count > 0
    
    def add_user(self, google_id, email):
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                                INSERT INTO users (google_id, email)
                                VALUES (%s, %s)
                            """, (google_id, email))
        except psycopg2.errors.UniqueViolation:
            raise ValueError(f"User {google_id}, email {email} already exists")
        
        self.conn.commit()
        cursor.close()
    
    def get_notes(self, google_id):
        cursor = self.conn.cursor()
        
        cursor.execute("""
                            SELECT notes
                            FROM users
                            WHERE google_id = %s
                        """, (google_id,))
        
        notes = cursor.fetchone()[0]
        
        cursor.close()
        
        return notes
    
    @staticmethod
    def _traverse_notes(notes, find_id):
        # employ a stack to non-recursively traverse the notes
        stack = collections.deque()
        stack.append(notes)
        
        while stack:
            current = stack.pop()
            
            if current["id"] == find_id:
                return current
            
            if current["type"] == "notebook":
                for note in current["notes"]:
                    stack.append(note)
        
        return None
    
    def modify_noteobject(self, google_id, note_id, new_note_data):
        cursor = self.conn.cursor()
        
        # get the notes, traverse them until we find the note with the given id
        # and replace it with the new note
        
        cursor.execute("""
                SELECT notes
                FROM users
                WHERE google_id = %s
            """, (google_id,))
        
        notes = cursor.fetchone()[0]
        
        note = self._traverse_notes(notes, note_id)
        
        if note is None:
            raise ValueError(f"Note with id {note_id} not found")
        
        if note["type"] == "note" and "content" in new_note_data:
            note["content"] = new_note_data["content"]
        
        if "title" in new_note_data:
            note["title"] = new_note_data["title"]
        
        cursor.execute("""
                UPDATE users
                SET notes = %s
                WHERE google_id = %s
            """, (json.dumps(notes), google_id))
        
        self.conn.commit()
        cursor.close()
    
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
    
    def _read_and_increment_id_counter(self, google_id) -> int:
        cursor = self.conn.cursor()
        
        cursor.execute("""
                            SELECT notes_id_counter
                            FROM users
                            WHERE google_id = %s
                        """, (google_id,))
        
        id_counter = cursor.fetchone()[0]
        
        cursor.execute("""
                UPDATE users
                SET notes_id_counter = notes_id_counter + 1
                WHERE google_id = %s
            """, (google_id,))
        
        cursor.close()
        
        return id_counter
    
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
            cursor.close()
            raise ValueError(f"User {google_id}, email {email} already exists")
        
        self.conn.commit()
        cursor.close()
    
    def get_note_by_id(self, google_id, note_id):
        cursor = self.conn.cursor()
        
        cursor.execute("""
                            SELECT notes
                            FROM users
                            WHERE google_id = %s
                        """, (google_id,))
        
        notes = cursor.fetchone()[0]
        
        cursor.close()
        
        return self._traverse_notes(notes, note_id)
    
    def get_total_notes(self, google_id) -> dict:
        """
        Gets the full notes object, including the content of the notes
        
        :param google_id: The Google id of the user
        :return: The notes object
        """
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
                            SELECT notes
                            FROM users
                            WHERE google_id = %s
                        """, (google_id,))
        
        notes = cursor.fetchone()[0]
        
        cursor.close()
        
        return notes
    
    def get_notes_no_content(self, google_id):
        notes = self.get_total_notes(google_id)
        
        # Delete notes content before sending them to the client to limit the amount of data sent
        def delete_content(note):
            print(note)
            
            if note["type"] == "note":
                print("deleting content")
                del note["content"]
            else:
                print("deleting more")
                for n in note["notes"]:
                    delete_content(n)
        
        delete_content(notes)
        
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
            cursor.close()
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
    
    def add_noteobject(self, google_id: str, parent: int, note_type: str) -> int:
        """
        Adds a new noteobject under the note with the given under_id.
        :param google_id: The Google id of the user
        :param parent: The id of the notebook under which to add the new noteobject
        :param note_type: The type of the note to add. Can be either "note" or "notebook
        :return: The id of the newly added noteobject
        """
        
        full_notes = self.get_total_notes(google_id)
        parent_notebook = self._traverse_notes(full_notes, parent)
        
        if parent_notebook is None or parent_notebook["type"] != "notebook":
            raise ValueError(f"Notebook with id {parent} not found")
        
        new_note = {
            "id": self._read_and_increment_id_counter(google_id),
            "type": note_type,
            "title": f"New Note{'book' if note_type == 'notebook' else ''}",
        }
        
        if note_type == "note":
            new_note["content"] = ""
        else:
            new_note["notes"] = []
        
        parent_notebook["notes"].append(new_note)
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
                UPDATE users
                SET notes = %s
                WHERE google_id = %s
            """, (json.dumps(full_notes), google_id))
        
        self.conn.commit()
        cursor.close()
        
        return new_note["id"]
    
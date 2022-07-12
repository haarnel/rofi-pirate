import pickle
import os
import sqlite3
from typing import List

from rofi_pirate.jackett import TorrentItem
from rofi_pirate.utils import get_timestamp


CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS torrents (
        timestamp INT,
        title TEXT UNIQUE,
        entry BLOB
    );
"""

CREATE_TABLE_QUERIES = """
    CREATE TABLE IF NOT EXISTS queries (
        timestamp INT,
        cquery TEXT UNIQUE
    );
"""

INSERT_ENTRY = """
    INSERT INTO torrents VALUES (?, ?, ?);
"""

INSERT_QUERY = """
    INSERT INTO queries VALUES (?, ?);
"""

class Database(object):
    
    def __init__(self, path: str):
        self.path = os.path.expanduser(path)
        self.connection = sqlite3.connect(self.path)
        self.cursor = self.connection.cursor()

        self.cursor.execute(CREATE_TABLE)
        self.cursor.execute(CREATE_TABLE_QUERIES)
        self.connection.commit()
    
    def add_torrent(self, torrent: TorrentItem) -> None:
        obj = pickle.dumps(torrent)
        try:
            self.cursor.execute(INSERT_ENTRY, (torrent.timestamp,  torrent.Title, sqlite3.Binary(obj)))
            self.connection.commit()
        except sqlite3.IntegrityError:
            pass

    def add_query(self, query: str) -> None:
        try:
            self.cursor.execute(INSERT_QUERY, (get_timestamp(), query))
            self.connection.commit()
        except sqlite3.IntegrityError:
            pass

    def update_timestamp(self, torrent: TorrentItem) -> None:
        prv_timestamp = torrent.timestamp
        torrent.timestamp = get_timestamp()
        self.cursor.execute("""UPDATE torrents SET timestamp = ? WHERE timestamp = ?""", (torrent.timestamp, prv_timestamp))
        self.connection.commit()

    def get_torrents(self) -> List[TorrentItem]:
        self.cursor.execute("SELECT * FROM torrents ORDER BY timestamp DESC;")
        rows = self.cursor.fetchall()
        torrents = []
        for row in rows:
            entry = pickle.loads(row[2])
            torrents.append(entry)
        return torrents

    def get_queries(self) -> List[str]:
        self.cursor.execute("SELECT * FROM queries ORDER BY timestamp DESC;")
        queries = []
        for query in self.cursor.fetchall():
            queries.append(query[-1])
        return queries
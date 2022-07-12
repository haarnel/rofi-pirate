from functools import partial
import os
import sys
import tempfile
from typing import List, Tuple
import webbrowser

import requests
from rofi_pirate.config import Config
import subprocess
from rofi_pirate.db import Database
from rofi_pirate.utils import file_size_format
from rofi_pirate.jackett import Jackett, Category, TorrentItem
from rofi_pirate.magnet import MagnetFinder

CATEGORY_CHOICE = {
    "aa": ["", "Everything", Category.EVERYTHING],
    "mv": ["ﳜ", "Movies", Category.MOVIES],
    "au": ["", "Audio", Category.AUDIO],
    "pc": ["", "PC", Category.PC],
    "tv": ["", "TV", Category.TV],
    "bb": ["", "Books", Category.BOOKS],
    "xx": ["", "XXX", Category.XXX],
    "ss": ["", "Other", Category.OTHER],
}

MENU_CHOICE = {
    "ss": ["", "New Search"],
    "hh": ["", "Search history"]
}

TORRENT_CHOICE = {
    "pp": ["喇", "Stream"],
    "oo": ["", "Open Resource Link"],
    "dd": ["", "Download torrent file"]
}


class Rofi:
    
    def __init__(self, config: Config):
        self.config = config
        self.jackett = Jackett(
            config.JACKETT_ENDPOINT,
            config.JACKETT_APIKEY,
        )
        self.db = Database(config.HISTORY_CACHE)

        # Current State.
        self.Category: Category = None
        self.Query: str = None
        self.Torrent: TorrentItem = None

        # Check Jackett
        ok = self.jackett._check_status()
        if not ok:
            msg = f"Jackett is not running\n\n{self.config.JACKETT_ENDPOINT}"
            self.send_notification(msg)
            print(f"Error: {msg}")
            sys.exit(1)


    def menu_step(self):
        choices = self._generate_choices(MENU_CHOICE)
        theme = self._set_theme_params(width=30, height=30)
        choice = self._get_choice("Menu", choices, theme)
        code = choice[:2]
        if code == "ss":
            return self.category_step
        if code == "hh":
            return self.history_step

    def category_step(self):
        categories = self._generate_choices(CATEGORY_CHOICE)
        theme = self._set_theme_params(width=40, height=27, columns=3, lines=4)
        category = self._get_choice("Category", categories, theme)
        category = CATEGORY_CHOICE.get(category[:2])
        if category is None or category[:2] == "jk":
            return self.menu_step
            
        self.Category = category[-1]
        return self.query_step
    
    def history_step(self):
        torrents = self.db.get_torrents()
        choices, torrents = self._get_torrent_dict(torrents)
        theme = self._set_theme_params(width=90, height=90, columns=1)
        choice = self._get_choice("History", choices, theme)
        if choice is None or choice[:2] == "jk":
            return self.menu_step
        else:
            torrent = torrents[choice.strip()]
            self.Torrent = torrent
            self.db.update_timestamp(self.Torrent)
            return partial(self.torrent_step, from_history=True)

    def query_step(self):
        theme = self._set_theme_params(width=30, height=50, columns=1, lines=10)
        queries = "\n".join(query for query in self.db.get_queries())
        query = self._get_choice(self.Category.name.capitalize(), queries, theme)
        query = query.strip()
        if query[:2] == "jk":
            return self.category_step
        if query:
            self.Query = query.strip()
            self.db.add_query(self.Query)
            return self.search_step
        else:
            return self.category_step

    def search_step(self):
        if self.Category == Category.EVERYTHING:
            categories = []
        else:
            categories = [self.Category]

        items = self.jackett.search(
            query=self.Query,
            categories=categories,
            limit=self.config.SEARCH_LIMIT,
        )
        torrents = {}
        torrents_str = ""
        for item in items:
            fmt_size = file_size_format(item.Size)
            key = f"[ S: {item.Seeders}  P: {item.Peers}] | Size: {fmt_size} | {item.Title} || {item.PublishDate} [{item.Tracker}]"
            torrents_str += key + '\n'
            torrents[key] = item

        theme = self._set_theme_params(width=90, height=90, columns=1)
        choice = self._get_choice("Results", torrents_str, theme)
        if choice[:2] == "jk":
            return self.query_step

        torrent = torrents[choice.strip()]
        if torrent is not None:
            self.Torrent= torrent
            return self.torrent_step
        else:
            return self.query_step

    def torrent_step(self, from_history: bool = False):
        choices = self._generate_choices(TORRENT_CHOICE)
        theme = self._set_theme_params(width=30, height=30, columns=1)
        choice = self._get_choice("Action", choices, theme)
        code = choice[:2]
        if code == "jk" and from_history:
            return self.history_step
        elif code == 'pp':
            if self.Torrent.MagnetLink is None:
                self.magnet_finder_step()
            else:
                self._play_torrent(update=from_history)
        elif code == "oo":
            self._open_link(self.Torrent.ResourceLink)
        elif code == "dd":
            if not self.Torrent.TorrentFileLink:
                self.send_notification("Error: Unable to get the torrent file\n.")
                self._open_link(self.Torrent.ResourceLink)
            else:
                self._download_torrent()
        else:
            return self.search_step

    def magnet_finder_step(self):
        found = MagnetFinder(self.Torrent)
        if found:
            self._play_torrent()
    
    def _get_input(self, prompt: str, theme: str = "", back: bool = True) -> str:
        command =  f'rofi -dmenu -p "{prompt}" -i -theme-str "{theme}"'
        if back:
            command = f'echo "jk)  Go back\n" | {command}'
        choice = subprocess.check_output(command, shell=True)
        return choice.decode()

    def _get_choice(self, prompt: str, choices: str, theme: str = "", back: bool = True) -> str:
        if back:
            choices = f"jk)  Go back\n{choices.lstrip()}" 
        command = f'echo "{choices}" | rofi -dmenu -p "{prompt}" -i -theme-str "{theme}"'
        choice = subprocess.check_output(command, shell=True)
        return choice.decode()
    
    def _generate_choices(self, choices: dict) -> str:
        return "\n".join(f"{key}) {value[0]} {value[1]}" for key, value in choices.items())
    
    def _play_torrent(self, update: bool = False) -> None:
        if update:
            self.db.update_timestamp(self.Torrent)
        else:
            self.db.add_torrent(self.Torrent)
        path = self.config.PEERFLIX_CACHE
        cache_path = os.path.expanduser(os.path.expanduser(path))
        command = f'{self.config.PEERFLIX_CMD} --path {cache_path} "{self.Torrent.MagnetLink}"'
        subprocess.Popen(command, shell=True, start_new_session=True)

    def _download_torrent(self) -> None:
        temp_file = tempfile.NamedTemporaryFile('wb', suffix='.torrent', delete=False)
        with requests.get(self.Torrent.TorrentFileLink, stream=True) as r:
            r.raise_for_status()
            with open(temp_file.name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):  
                    f.write(chunk)
        command = f'xdg-open "{temp_file.name}"'
        subprocess.Popen(command, shell=True)

    def _set_theme_params(self, columns: int = 2, lines: int = 15, width: int = 90, height: int = 90):
        return f'window {{ width: {width}%; height: {height}%; }} listview {{ columns: {columns}; lines: {lines}; }}'
    
    def _get_torrent_dict(self, torrents: List[TorrentItem]) -> Tuple[str, dict]:
        torrents_str = ""
        items = {}
        for item in torrents:
            fmt_size = file_size_format(item.Size)
            key = f"{item.Title}".strip()
            torrents_str += key + '\n'
            items[key] = item

        return torrents_str.rstrip(), items

    def send_notification(self, text: str) -> None:
        command = f'notify-send "{text}"'
        subprocess.Popen(command, shell=True)
    
    def _open_link(self, link: str) -> None:
        webbrowser.open(link)

    def run(self):
        next = self.menu_step()
        while True:
            if next is not None:
                next = next()
            else:
                sys.exit(0)
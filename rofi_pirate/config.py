import json
import os
from pathlib import Path


class Config(object):

    def __init__(self):
        self.JACKETT_ENDPOINT = 'http://127.0.0.1:9117'
        self.JACKETT_APIKEY = '<API-KEY>'
        self.SEARCH_LIMIT = 25
        self.PEERFLIX_CMD = "peerflix -t -k -a"
        self.HISTORY_CACHE = None
        self.PEERFLIX_CACHE = None

    def load_config(self) -> None:
        path = os.path.expanduser("~/.config/rofi_pirate/config.json")
        with open(path, 'r') as file:
            config = json.load(file)
            self.__dict__.update(**config)
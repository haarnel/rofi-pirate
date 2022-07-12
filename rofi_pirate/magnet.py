import re

import requests
from bs4 import BeautifulSoup

from rofi_pirate.jackett import TorrentItem


class BaseTracker(object):
    def __init__(self, torrent: TorrentItem) -> None:
        self._torrent = torrent

    def get_html(self) -> str | None:
        torrent_url = self._torrent.ResourceLink
        response = requests.get(torrent_url)
        if response.ok:
            return response.text
        return None

    def find_magnet_link(self) -> str | None:
        html = self.get_html()
        if html is not None:
            return self.extract_magnet_link(html)
        else:
            return None

    def extract_magnet_link(self, html: str) -> str:
        """Base Implementation of extract magnet link. You can override this method if you need."""
        soup_obj = self.get_soup_obj(html)
        links = soup_obj.find_all("a", href=True)
        for link in links:
            href = link.get("href")
            if href.startswith("magnet"):
                return href

    def get_soup_obj(self, html: str) -> BeautifulSoup:
        soup = BeautifulSoup(html, "html.parser")
        return soup


class Tracker_1337x(BaseTracker):
    """Ex: https://1337x.to"""

    pass


class NoNaMeClub(BaseTracker):
    def extract_link(self, html: str) -> str:
        soup_obj = self.get_soup_obj(html)
        link = soup_obj.find("a", attrs={"title": "Примагнититься"})
        if link is not None:
            link = link.get("href")
            if link.startswith("magnet"):
                return link


class LimeTorrents(BaseTracker):
    def extract_link(self, html: str) -> str:
        soup_obj = self.get_soup_obj(html)
        link = soup_obj.find("a", text=re.compile("^magnet$", re.I))
        if link is not None:
            link = link.get("href")
            if link.startswith("magnet"):
                return link


def MagnetFinder(torrent: TorrentItem) -> bool:
    tracker: BaseTracker = None
    if torrent.Tracker == "1337x":
        tracker = Tracker_1337x(torrent)
    elif torrent.Tracker == "NoNaMe Club":
        tracker = NoNaMeClub(torrent)
    elif torrent.Tracker == "LimeTorrents":
        tracker = LimeTorrents(torrent)

    if tracker is None:
        return False

    link = tracker.find_magnet_link()

    if link is not None:
        torrent.MagnetLink = link
        return True

    return False
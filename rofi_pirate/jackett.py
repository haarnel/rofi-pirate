import typing as t
from datetime import datetime
from enum import IntEnum
from textwrap import dedent

import requests
from dateutil import parser
from operator import attrgetter

from rofi_pirate.utils import file_size_format, get_timestamp


class Category(IntEnum):
    EVERYTHING = 0
    MOVIES = 2000
    AUDIO = 3000
    PC = 4000
    TV = 5000
    XXX = 6000
    BOOKS = 7000
    OTHER = 8000


class TorrentItem:
    def __init__(
        self,
        Title: str,
        Tracker: str,
        ResourceLink: str,
        TorrentFileLink: str,
        MagnetLink: str,
        Peers: int,
        Seeders: int,
        Size: int,
        PublishDate: datetime,
    ):
        self.Title = Title
        self.Tracker = Tracker
        self.ResourceLink = ResourceLink
        self.TorrentFileLink = TorrentFileLink
        self.MagnetLink = MagnetLink
        self.Peers = Peers
        self.Seeders = Seeders
        self.Size = Size
        self.PublishDate = PublishDate

        self.timestamp = get_timestamp()


    def __str__(self):
        return dedent(
            f"""
            Tracker: {self.Tracker}
            Title: {self.Title}
            Published: {self.PublishDate}
            Size: {file_size_format(self.Size)}
            Seders/Peers: {self.Seeders}/{self.Peers}
            ResourceLink: {self.ResourceLink}
            TorrentFileLink: {self.TorrentFileLink}
            MagnetLink: {self.MagnetLink}
        """
        )


class Jackett(object):
    def __init__(
        self,
        Endpoint: str,
        ApiKey: str,
        Trackers: t.Optional[t.List[str]] = None,
        Categories: t.Optional[t.List[Category]] = None,
    ):
        self.Endpoint = Endpoint
        self.ApiKey = ApiKey
        self.Trackers = Trackers or []
        self.Categories = Categories or []
        self.session = requests.Session()

    def search(
        self,
        query: str,
        limit: int = 25,
        sort_by: str = "Seeders",
        magnet_finder: t.Optional[bool] = False,
        categories: t.Optional[t.List[Category]] = None,
        trackers: t.Optional[str] = None,
    ) -> t.List[TorrentItem]:
        params = [
            ("apikey", self.ApiKey),
            ("Query", query.strip()),
        ]
        if categories is not None:
            for category in categories:
                params.append(("Category[]", str(category.value)))
        else:
            for category in self.Categories:
                params.append(("Category[]", str(category.value)))

        if trackers is not None:
            for tracker in trackers:
                params.append(("Tracker[]", str(tracker)))
        else:
            for tracker in self.Trackers:
                params.append(("Tracker[]", str(tracker)))

        url = self.Endpoint + "/api/v2.0/indexers/all/results"

        response = self.session.get(url, params=params)
        items = self._parse_items(response.json())
        if sort_by is not None:
            items.sort(key=attrgetter(sort_by), reverse=True)

        return items[:limit]


    def _parse_items(self, data: dict) -> t.List[TorrentItem]:
        results: t.List[t.Dict] = data["Results"]
        parsed_items = []
        for result in results:
            publish_date = parser.parse(result["PublishDate"])
            item = {
                "Title": result["Title"].strip(),
                "Tracker": result["Tracker"],
                "ResourceLink": result["Details"],
                "TorrentFileLink": result["Link"],
                "MagnetLink": result["MagnetUri"],
                "Size": result["Size"],
                "Peers": result["Peers"],
                "Seeders": result["Seeders"],
                "PublishDate": publish_date,
            }
            parsed_items.append(TorrentItem(**item))

        return parsed_items

    def _check_status(self) -> bool:
        try:
            self.session.get(self.Endpoint)
        except requests.ConnectionError:
            return False
        return True
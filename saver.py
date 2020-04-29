#!/usr/bin/env python

from __future__ import annotations
import logging
import pathlib
import datetime
from typing import Tuple


# Setup logging
logger = logging.getLogger(__name__)


class Saver:
    """
    Saves messages from the socket for permanent record.
    """
    def __init__(self, path_to_folder: pathlib.Path):
        self.parent = path_to_folder.expanduser()
        self.heartbeats = self.parent / pathlib.Path("heartbeats")
        self.orders = self.parent / pathlib.Path("orders")
        self.prices = self.parent / pathlib.Path("prices")
        self.symbols = self.parent / pathlib.Path("symbols")
        self.ticker = self.parent / pathlib.Path("ticker")
        self.trades = self.parent / pathlib.Path("trades")
        self.subfolders = (self.heartbeats, self.orders, self.prices, self.symbols, self.ticker, self.trades)
        self.create_folders((self.parent, *self.subfolders))
        self.channels = dict(zip(("heartbeat", "l3", "prices", "symbols", "ticker", "trades"), self.subfolders))
        self.weekdays = dict(zip(range(7), ("SU", "MO", "TU", "WE", "TH", "FR", "SA")))
        self.create_file_paths()
    def __enter__(self) -> Saver:
        logger.debug("Entering Saver")
        self.hbf = open(self.heartbeats_file_path, mode="wb")
        return self
    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        logger.debug("Leaving Saver")
        self.hbf.flush()
        self.hbf.close()
        return False
    def create_folders(self, folders: Tuple[pathlib.Path]):
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
    def create_file_paths(self):
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            self.heartbeats_file_path = self.heartbeats / f"{now.strftime('%Y%m%d')}{self.weekdays[int(now.strftime('%w'))]}{now.strftime('%H%M%S')}.hb"
    def save(self, msg):
        self.hbf.write(str.encode(repr(msg) + "\n", encoding="utf-8"))


if __name__ == "__main__":
    pass

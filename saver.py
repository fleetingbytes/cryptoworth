#!/usr/bin/env python

from __future__ import annotations
import itertools
import json
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
        self.started = datetime.datetime.now(tz=datetime.timezone.utc)
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
        self.counter = itertools.count()
        self.now = datetime.datetime.now(tz=datetime.timezone.utc)
    def __enter__(self) -> Saver:
        logger.debug("Entering Saver")
        self.hbf = open(self.heartbeats_file_path, mode="w")
        logger.debug(f"Opened {self.hbf.name}")
        self.syf = open(self.symbols_file_path, mode="w")
        logger.debug(f"Opened {self.syf.name}")
        self.pxf = open(self.prices_file_path, mode="w")
        logger.debug(f"Opened {self.pxf.name}")
        self.tkf = open(self.ticker_file_path, mode="w")
        logger.debug(f"Opened {self.tkf.name}")
        self.trf = open(self.trades_file_path, mode="w")
        logger.debug(f"Opened {self.trf.name}")
        self.orf = open(self.orders_file_path, mode="w")
        logger.debug(f"Opened {self.orf.name}")
        return self
    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        for fd in (self.hbf, self.syf, self.pxf, self.tkf, self.trf, self.orf):
            fd.flush()
            fd.close()
            logger.debug(f"Saved {fd.name}")
        logger.debug("Leaving Saver")
        return False
    def format_datetime(self, dt: datetime.datetime):
        return f"{dt.strftime('%Y%m%d')}{self.weekdays[int(dt.strftime('%w'))]}{dt.strftime('%H%M%S')}"
    def create_folders(self, folders: Tuple[pathlib.Path]):
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
    def create_file_paths(self):
            self.heartbeats_file_path = self.heartbeats / (self.format_datetime(self.started) + ".hb")
            self.symbols_file_path = self.symbols / (self.format_datetime(self.started) + ".sy")
            self.prices_file_path = self.prices / (self.format_datetime(self.started) + ".px")
            self.ticker_file_path = self.ticker / (self.format_datetime(self.started) + ".tk")
            self.trades_file_path = self.trades / (self.format_datetime(self.started) + ".tr")
            self.orders_file_path = self.orders / (self.format_datetime(self.started) + ".or")
    def dump_dict_as_json(self, d: Mapping[str, str], fd: io.BufferedWriter):
        print(self.format_datetime(datetime.datetime.now(tz=datetime.timezone.utc)), file=fd)
        json.dump(d, fd, indent=4, separators=(",", ": "))
        print("\n", file=fd)
    def save_hb(self, msg: Mapping[str, str]):
        self.dump_dict_as_json(msg, self.hbf)
    def save_sy(self, msg: Mapping[str, str]):
        self.dump_dict_as_json(msg, self.syf)
    def save_px(self, msg: Mapping[str, str]):
        self.dump_dict_as_json(msg, self.pxf)
    def save_tk(self, msg: Mapping[str, str]):
        self.dump_dict_as_json(msg, self.tkf)
    def save_tr(self, msg: Mapping[str, str]):
        self.dump_dict_as_json(msg, self.trf)
    def save_or(self, msg: Mapping[str, str]):
        self.dump_dict_as_json(msg, self.orf)
    def save(self, msg):
        if msg["channel"] == "l3":
            save_target = self.save_or
        elif msg["channel"] == "heartbeat":
            save_target = self.save_hb
        elif msg["channel"] == "prices":
            save_target = self.save_px
        elif msg["channel"] == "ticker":
            save_target = self.save_tk
        elif msg["channel"] == "trades":
            save_target = self.save_tr
        elif msg["channel"] == "symbols":
            save_target = self.save_sy
        save_target(msg)
        current_message_count = next(self.counter)
        self.now = datetime.datetime.now(tz=datetime.timezone.utc)
        delta = self.now - self.started
        try:
            if delta.seconds % 53 == 0:
                logger.debug(f"Message count: {current_message_count}, {msg['seqnum']}")
        except AttributeError:
            pass


if __name__ == "__main__":
    pass

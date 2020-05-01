#!/usr/bin/env python
# classes.py

import dataclasses
import logging
from collections import OrderedDict
from typing import List
from typing import Mapping
from typing import Union

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Order_Book:
    """
    Holds a list of bids and a list of asks for a particular symbol
    """
    bids: OrderedDict = dataclasses.field(default_factory=OrderedDict)
    asks: OrderedDict = dataclasses.field(default_factory=OrderedDict)
    def sum_orders(self) -> OrderedDict:
        """
        outputs bids or asks as level2 (summed to price levels)
        """
        for order_type in (self.bids, self.asks):
            px_qty = OrderedDict()
            for order in sorted(order_type.values(), reverse=True, key=lambda order: order.px):
                try:
                    px_qty[order.px] = px_qty[order.px] + order.qty
                except KeyError:
                    px_qty[order.px] = order.qty
            yield px_qty


@dataclasses.dataclass(frozen=True)
class Order:
    """
    Holds either a bid or an ask
    """
    id: int
    px: float
    qty: float


@dataclasses.dataclass
class Wallet:
    name: str
    dollar: float = 0
    euro: float = 0
    bitcoin: float = 0
    ether: float = 0
    litecoin: float = 0


@dataclasses.dataclass
class Message:
    seqnum: str = ""
    event: str = ""
    channel: str = ""
    timestamp: str = ""
    symbol: str = ""
    bids: List[Mapping[str, Union[str, float, int]]] = dataclasses.field(default_factory=list)
    asks: List[Mapping[str, Union[str, float, int]]] = dataclasses.field(default_factory=list)


class Exchange:
    """
    Holds the Order Books for several symbols in a stock exchange.
    A stock exchange in this case is one particular exchange server, 
    e.g. `exchange.blockchain.com`
    """
    def __init__(self, symbols):
        self.symbols = symbols
        self.order_books = dict(zip((symbol for symbol in self.symbols), (Order_Book() for symbol in self.symbols)))
    def evaluate(self, w: Wallet):
        logger.debug(f"Evaluating wallet")
        for ob in self.order_books.values():
            bids, asks = ob.sum_orders()
    def process_update(self, message):
        symbol = message["symbol"]
        bids = message["bids"]
        asks = message["asks"]
        for bid in bids:
            if bid["qty"] == 0:
                del(self.order_books[symbol].bids[bid["id"]])
            else:
                self.order_books[symbol].bids[bid["id"]] = Order(**bid)
        for ask in asks:
            if ask["qty"] == 0:
                del(self.order_books[symbol].asks[ask["id"]])
            else:
                self.order_books[symbol].asks[ask["id"]] = Order(**ask)
    def process_subscribed(self, message):
        logger.debug(f"Subscribed to {message['symbol']}")
    def process_unknown(self, message):
        logger.debug("Unknown message:")
        logger.debug(message)
    def process(self, message):
        if message.get("event") in ("updated", "snapshot"):
            self.process_update(message)
        elif message.get("event") == "subscribed":
            self.process_subscribed(message)
        else:
            process_unknown(message)


if __name__ == "__main__":
    pass

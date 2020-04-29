#!/usr/bin/env python
import json
import math
import dataclasses
import pathlib
# https://github.com/websocket-client/websocket-client
from websocket import create_connection

#Own modules:
import logging
import logging.config
import logging_conf

# setup logging
logging.config.dictConfig(logging_conf.create_dict_config(pathlib.Path(pathlib.Path.cwd()), "all.log", "errors.log"))
logger = logging.getLogger(__name__)


options = dict()
options['origin'] = 'https://exchange.blockchain.com'
url = "wss://ws.prod.blockchain.info/mercury-gateway/v1/ws"
ws = create_connection(url, **options)
symbols = ("LTC-EUR", )
# symbols = ("ETH-EUR", "LTC-EUR")
messages = ['{"action": "subscribe", "symbol": "' + "{}".format(symbol) + '", "channel": "l2"}' for symbol in symbols]


@dataclasses.dataclass
class Order_Book:
    """
    Holds a list of bids and a list of asks for a particular symbol
    """
    bids: dict = dataclasses.field(default_factory=dict)
    asks: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True)
class Order:
    """
    Holds either a bid or an ask
    """
    num: int
    qty: float


@dataclasses.dataclass
class Wallet:
    name: str
    dollars: float = 0
    bitcoin: float = 0
    ether: float = 0
    litecoin: float = 0


class Exchange:
    """
    Holds the Order Books for several symbols in a stock exchange.
    A stock exchange in this case is one particular exchange server, 
    e.g. `exchange.blockchain.com`
    """
    def __init__(self, symbols):
        self.symbols = symbols
        self.order_books = dict(zip((symbol for symbol in self.symbols), (Order_Book() for symbol in self.symbols)))
    def process_update(self, message):
        for bid in message["bids"]:
            if bid["qty"] == 0:
                del(self.order_books[message["symbol"]].bids[bid["px"]])
            else:
                self.order_books[message["symbol"]].bids[bid["px"]] = Order(num=bid["num"], qty=bid["qty"])
        for ask in message["asks"]:
            if ask["qty"] == 0:
                del(self.order_books[message["symbol"]].asks[ask["px"]])
            else:
                self.order_books[message["symbol"]].asks[ask["px"]] = Order(num=ask["num"], qty=ask["qty"])
        logger.debug(f"{message['symbol']} Bids:")
        for price, order in sorted(self.order_books[message["symbol"]].bids.items(), reverse=True):
            logger.debug(f"{price}: {order.qty}")
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


def get_l2(ws, messages):
    for msg in messages:
        ws.send(msg)
    try:
        while True:
            result =  ws.recv()
            j = json.loads(result)
            yield j
    except KeyboardInterrupt:
        ws.close()


if __name__ == "__main__":
    exchange = Exchange(symbols)
    for l2message in get_l2(ws, messages):
        exchange.process(l2message)

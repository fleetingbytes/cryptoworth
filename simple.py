#!/usr/bin/env python

import dataclasses
import itertools
import json
import logging
import logging.config
import math
import pathlib
# https://github.com/websocket-client/websocket-client
from collections import OrderedDict
from typing import List, Mapping, Union
from websocket import create_connection

#Own modules:
import logging_conf
import saver

# setup logging
logging.config.dictConfig(logging_conf.create_dict_config(pathlib.Path(pathlib.Path.cwd()), "all.log", "errors.log"))
logger = logging.getLogger(__name__)


options = dict()
options['origin'] = 'https://exchange.blockchain.com'
url = "wss://ws.prod.blockchain.info/mercury-gateway/v1/ws"
ws = create_connection(url, **options)
symbols = ("BTC-EUR", )
# symbols = ("BTC-EUR", "ETH-EUR", "LTC-EUR")
messages = [] + \
           ['{"action": "subscribe", "channel": "l3", "symbol": "' + f"{symbol}" + '"}' for symbol in symbols]

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
            breakpoint()
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


def listen(ws, messages):
    for msg in messages:
        ws.send(msg)
    try:
        while True:
            result =  ws.recv()
            j = json.loads(result)
            yield j
    except KeyboardInterrupt:
        ws.close()


def wait_key() -> str:
    """
    Wait for a key press on the console and return it.
    """
    result = None
    if os.name == 'nt':
        import msvcrt
        result = msvcrt.getch()
    else:
        import termios
        fd = sys.stdin.fileno()
        oldterm = termios.tcgetattr(fd)
        newattr = termios.tcgetattr(fd)
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, newattr)
        try:
            result = sys.stdin.read(1)
        except IOError:
            pass
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
    return str(result, encoding="utf-8").upper()


myWallet = Wallet(name="Sven's wallet",
                  dollar=5.21, 
                  euro=0.29, 
                  bitcoin=3.70511573+0.0599833+0.094, 
                  ether=12.65+0.03, 
                  litecoin=79.691+0.1)


if __name__ == "__main__":
    for message in messages:
        logger.debug(message)
    exchange = Exchange(symbols)
    with saver.Saver(pathlib.Path("~/exchange_data")) as svr:
        try:
            for message in listen(ws, messages):
                svr.save(message)
                exchange.process(message)
                exchange.evaluate(myWallet)
        except KeyboardInterrupt:
            logger.debug("Cought Keyboard Interrupt, quitting.")

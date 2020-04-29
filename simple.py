#!/usr/bin/env python

import dataclasses
import json
import logging
import logging.config
import math
import pathlib
# https://github.com/websocket-client/websocket-client
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
symbols = ("ETH-EUR", )
# symbols = ("ETH-EUR", "LTC-EUR")
messages = ['{"action": "subscribe",  "channel": "heartbeat"}']
           # ['{"action": "subscribe", "symbol": "' + "{}".format(symbol) + '", "channel": "l3"}' for symbol in symbols] +


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
    id: int
    px: float
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
                del(self.order_books[message["symbol"]].bids[bid["id"]])
            else:
                self.order_books[message["symbol"]].bids[bid["id"]] = Order(**bid)
        for ask in message["asks"]:
            if ask["qty"] == 0:
                del(self.order_books[message["symbol"]].asks[ask["px"]])
            else:
                self.order_books[message["symbol"]].asks[ask["px"]] = Order(**ask)
        logger.debug(f"{message['symbol']} Bids:")
        for order in sorted(self.order_books[message["symbol"]].bids.values(), reverse=True, key=lambda order: order.px):
            logger.debug(f"Price: {order.px}, Quantity: {order.qty}, Id: {order.id}")
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


if __name__ == "__main__":
    exchange = Exchange(symbols)
    with saver.Saver(pathlib.Path("~/exchange_data")) as svr:
        try:
            for message in listen(ws, messages):
                svr.save(message)
            # exchange.process(message)
        except KeyboardInterrupt:
            logger.debug("Cought Keyboard Interrupt, quitting.")

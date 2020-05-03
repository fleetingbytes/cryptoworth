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
    symbol: str
    bids: OrderedDict = dataclasses.field(default_factory=OrderedDict)
    asks: OrderedDict = dataclasses.field(default_factory=OrderedDict)
    l2bids: OrderedDict = dataclasses.field(default_factory=OrderedDict)
    l2asks: OrderedDict = dataclasses.field(default_factory=OrderedDict)
    def sum_orders(self) -> OrderedDict:
        """
        outputs bids or asks as level2 (summed to price levels)
        """
        for order_type, reverse in zip((self.bids, self.asks), (True, False)):
            px_qty = OrderedDict()
            for order in sorted(order_type.values(), reverse=reverse, key=lambda order: order.px):
                try:
                    px_qty[order.px] = px_qty[order.px] + order.qty
                except KeyError:
                    px_qty[order.px] = order.qty
            yield px_qty
    def make_l2(self):
        self.l2bids, self.l2asks = self.sum_orders()


@dataclasses.dataclass(frozen=True)
class Order:
    """
    Holds either a bid or an ask
    """
    id: int
    px: float
    qty: float


@dataclasses.dataclass
class Currency:
    name: str
    symbol: str
    unit: str


@dataclasses.dataclass
class Wallet:
    name: str
    curr_amounts: dataclasses.InitVar[Mapping[str, float]]
    currencies: Mapping[str, Currency] = dataclasses.field(init=False)
    amounts: Mapping[str, float] = dataclasses.field(init=False)
    values: Mapping[str, float] = dataclasses.field(init=False)
    def __post_init__(self, curr_amounts):
        dollar = Currency(name="dollar", symbol="USD", unit="$")
        euro = Currency(name="euro", symbol="EUR", unit="€")
        bitcoin = Currency(name="bitcoin", symbol="BTC", unit="₿")
        ether = Currency(name="ether", symbol="ETH", unit="Ξ")
        litecoin = Currency(name="litecoin", symbol="LTC", unit="Ł")
        symbols = ("USD", "EUR", "BTC", "ETH", "LTC")
        curr = (dollar, euro, bitcoin, ether, litecoin)
        possible_currencies = dict(zip(symbols, curr))
        self.currencies = dict()
        self.amounts = dict()
        self.values = dict()
        for symbol, amount in curr_amounts.items():
            logger.debug(f"curr_amount: {symbol}: {amount}")
            try:
                self.currencies[symbol] = possible_currencies[symbol]
                self.amounts[symbol] = amount
                self.values[symbol] = 0
            except KeyError:
                logger.error(f"Currency {symbol} not implemented.")


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
        self.order_books = dict(zip((symbol for symbol in self.symbols), (Order_Book(symbol=symbol) for symbol in self.symbols)))
    def cascaded_trade(self, to_sell: float, orders: Mapping[float, float], direction: bool, ob_symbol: str):
        if direction:
            selling_currency = ob_symbol.split("-")[0]
            buying_currency = ob_symbol.split("-")[1]
        else:
            selling_currency = ob_symbol.split("-")[0]
            buying_currency = ob_symbol.split("-")[1]
        offers = sorted(orders.items(), reverse=not direction)
        still_to_sell = to_sell
        sold_value = 0
        while still_to_sell > 0:
            if direction:
                try:
                    price, available = offers.pop()
                    logger.debug(f"Best offer is buying {available} {selling_currency} at a price of {price} {buying_currency} per 1 {selling_currency}.")
                    selling = min(still_to_sell, available)
                    logger.debug(f"Can sell {selling} {selling_currency}")
                    trade_value = price * selling
                    logger.debug(f"Selling {selling} {selling_currency} for {trade_value} {buying_currency}.")
                    still_to_sell = still_to_sell - selling
                    sold_value = sold_value + trade_value
                    logger.debug(f"Total sold {to_sell - still_to_sell} {selling_currency}, for {sold_value} {buying_currency}")
                    logger.debug(f"Still to sell {still_to_sell} {selling_currency}.")
                except IndexError:
                    logger.error(f"Cannot trade remaining {still_to_sell} {selling_currency}. No more bids.")
                    break
            else:
                try:
                    price, available = offers.pop()
                    logger.debug(f"Best offer is selling {available} {selling_currency} at a price of {price} {buying_currency} per 1 {selling_currency}")
                    logger.debug(f"{still_to_sell} {buying_currency} could buy me {still_to_sell / price} {selling_currency}.")
                    selling = min(available, still_to_sell / price)
                    logger.debug(f"min({available}, {still_to_sell / price})")
                    logger.debug(f"Can buy some {selling_currency} for {still_to_sell} {buying_currency} at a price of {price} {buying_currency} per 1 {selling_currency}.")
                    trade_value = selling / price
                    logger.debug(f"Buying {selling} {selling_currency} for ?.")
                    still_to_sell = still_to_sell - selling
                    sold_value = sold_value + trade_value
                    logger.debug(f"Total sold {to_sell - still_to_sell} {buying_currency}, for {sold_value} {selling_currency}")
                    logger.debug(f"Still to sell {still_to_sell} {buying_currency}.")
                except IndexError:
                    logger.error(f"Cannot trade remaining {still_to_sell} {buying_currency}. No more asks.")
                    break
        return sold_value, still_to_sell
    def change_currency (self, wallet: Wallet, source: str, target: str):
        """
        Changes currency from one to another using an orderbook
        """
        try:
            ob_symbol = "-".join((source, target))
            ob = self.order_books[ob_symbol]
            direction = True
        except KeyError:
            ob_symbol = "-".join((target, source))
            ob = self.order_books[ob_symbol]
            direction = False
        ob.make_l2()
        if direction:
            logger.debug(f"Bids would buy this much {source}, give this much {target} per 1 {source}.")
            orders = ob.l2bids
        else:
            logger.debug(f"Asks would sell this much {target}, give this much {source} per 1 {target}.")
            orders = ob.l2asks
        sold_value, still_to_sell = self.cascaded_trade(wallet.amounts[source], orders, direction, ob_symbol)
        wallet.values[target] = sold_value
        return sold_value
    def evaluate(self, wallet: Wallet):
        # logger.debug(f"Evaluating wallet by buying EUR")
        sold_value_BTC = self.change_currency(wallet, "BTC", "EUR")
        sold_value_ETH = self.change_currency(wallet, "ETH", "EUR")
        sold_value_LTC = self.change_currency(wallet, "LTC", "EUR")
        logger.info(f"Total value: {sold_value_BTC + sold_value_ETH + sold_value_LTC}")
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

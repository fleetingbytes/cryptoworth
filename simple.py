#!/usr/bin/env python
# simple.py

import itertools
import json
import logging
import logging.config
import math
import pathlib

#Own modules:
import classes
import logging_conf
import saver
import servers


# setup logging
logging.config.dictConfig(logging_conf.create_dict_config(pathlib.Path(pathlib.Path.cwd()), "all.log", "errors.log"))
logger = logging.getLogger(__name__)


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


myWallet = classes.Wallet(name="Sven's wallet",
                          dollar=5.21, 
                          euro=0.29, 
                          bitcoin=3.70511573+0.0599833+0.094, 
                          ether=12.65+0.03, 
                          litecoin=79.691+0.1)


symbols = ("BTC-EUR", )
# symbols = ("BTC-EUR", "ETH-EUR", "LTC-EUR")
subscriptions = [] + \
                ['{"action": "subscribe", "channel": "l3", "symbol": "' + f"{symbol}" + '"}' for symbol in symbols]


if __name__ == "__main__":
    for sub in subscriptions:
        logger.debug(sub)
    exchange = classes.Exchange(symbols)
    with saver.Saver(pathlib.Path("~/exchange_data")) as svr:
        try:
            server = servers.Exchange_Blockchain(subscriptions)
            for message in server.listen():
                svr.save(message)
                exchange.process(message)
                exchange.evaluate(myWallet)
        except KeyboardInterrupt:
            logger.debug("Cought Keyboard Interrupt, quitting.")

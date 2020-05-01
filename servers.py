#!/usr/bin/env python
# servers.py

import json
import logging
# https://github.com/websocket-client/websocket-client
import websocket


logger = logging.getLogger(__name__)


class Exchange_Blockchain:
    def __init__(self, subscriptions):
        self.subscriptions = subscriptions
        self.options = dict()
        self.options["origin"] = "https://exchange.blockchain.com"
        self.url = "wss://ws.prod.blockchain.info/mercury-gateway/v1/ws"
        self.ws = websocket.create_connection(self.url, **self.options)
    def listen(self):
        for sub in self.subscriptions:
            self.ws.send(sub)
        try:
            while True:
                result = self.ws.recv()
                j = json.loads(result)
                yield j
        except KeyboardInterrupt:
            logger.debug("Cought Keyboard Interrupt, closing websocket.")
            self.ws.close()


if __name__ == "__main__":
    pass

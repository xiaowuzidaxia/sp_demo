#coding:utf-8
from xmlrpc.server import SimpleXMLRPCServer
import selectors
import os

if hasattr(selectors, 'PollSelector'):
    _ServerSelector = selectors.PollSelector
else:
    _ServerSelector = selectors.SelectSelector


class ForkXMLRPCServer(SimpleXMLRPCServer):

    def check_process(self):
        raise NotImplementedError

    def add_pipes(self, register):
        raise NotImplementedError

    def serve_forever(self, poll_interval=0.5):
        """Handle one request at a time until shutdown.

        Polls for shutdown every poll_interval seconds. Ignores
        self.timeout. If you need to do periodic tasks, do them in
        another thread.
        """
        # self.__is_shut_down.clear()
        try:
            # XXX: Consider using another file descriptor or connecting to the
            # socket to wake this up instead of polling. Polling reduces our
            # responsiveness to a shutdown request and wastes cpu at all other
            # times.
            with _ServerSelector() as selector:
                selector.register(self, selectors.EVENT_READ)
                # self.add_pipes(selector)
                while True:
                    ready = selector.select(poll_interval)
                    print("true ready :", ready)
                    if ready:
                        print("ready: ", ready)
                        self._handle_request_noblock()
                    self.service_actions()
                    self.check_process()
        finally:
            # self.__shutdown_request = False
            # self.__is_shut_down.set()
            pass


if __name__ == "__main__":
    server = ForkXMLRPCServer(("127.0.0.1", 8003))
    def add(x, y):
        return x+y
    def sub(x, y):
        return x-y
    server.register_multicall_functions()
    server.register_function(add, "add")
    server.register_function(sub, "sub")
    server.serve_forever()
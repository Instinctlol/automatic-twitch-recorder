import threading

import ATRHandler
import utils
from atr_cmd import AtrCmd
from daemon import Daemon

if __name__ == '__main__':
    utils.get_client_id()  # creates necessary config before launch
    server = Daemon(('127.0.0.1', 1234), ATRHandler.ATRHandler)
    threading.Thread(target=server.serve_forever).start()
    AtrCmd().cmdloop_with_keyboard_interrupt()

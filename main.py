import threading

import automatic_twitch_recorder.ATRHandler
import automatic_twitch_recorder.utils
from automatic_twitch_recorder.atr_cmd import AtrCmd
from automatic_twitch_recorder.daemon import Daemon

if __name__ == '__main__':
    automatic_twitch_recorder.utils.get_client_id()  # creates necessary config before launch
    server = Daemon(('127.0.0.1', 1234), automatic_twitch_recorder.ATRHandler.ATRHandler)
    threading.Thread(target=server.serve_forever).start()
    AtrCmd().cmdloop_with_keyboard_interrupt()

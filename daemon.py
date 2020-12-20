import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from http.server import HTTPServer

import ATRHandler
import twitch
from utils import get_client_id, StreamQualities
from watcher import Watcher

class Daemon(HTTPServer):
    #
    # CONSTANTS
    #
    VALID_BROADCAST = ['live']  # 'rerun' can be added through commandline flags/options
    WEBHOOK_SECRET = 'automaticTwitchRecorder'
    WEBHOOK_URL_PREFIX = 'https://api.twitch.tv/helix/streams?user_id='
    LEASE_SECONDS = 864000  # 10 days = 864000
    check_interval = 10

    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.PORT = server_address[1]
        self.streamers = {}  # holds all streamers that need to be surveilled
        self.watched_streamers = {}  # holds all live streamers that are currently being recorded
        self.client_id = get_client_id()
        self.kill = False
        self.started = False
        self.download_folder = os.getcwd() + os.path.sep + "#streamer#"
        # ThreadPoolExecutor(max_workers): If max_workers is None or not given, it will default to the number of
        # processors on the machine, multiplied by 5
        self.pool = ThreadPoolExecutor()

    def add_streamer(self, streamer, quality=StreamQualities.BEST.value):
        streamer = streamer.lower()
        streamer_dict = {}
        resp = []
        ok = False
        qualities = [q.value for q in StreamQualities]
        if quality not in qualities:
            resp.append('Invalid quality: ' + quality + '.')
            resp.append('Quality options: ' + str(qualities))
        else:
            streamer_dict.update({'preferred_quality': quality})

            # get channel id of streamer
            user_info = list(twitch.get_user_info(streamer))

            # check if user exists
            if user_info:
                streamer_dict.update({'user_info': user_info[0]})
                self.streamers.update({streamer: streamer_dict})
                resp.append('Successfully added ' + streamer + ' to watchlist.')
                ok = True
            else:
                resp.append('Invalid streamer name: ' + streamer + '.')
        return ok, resp

    def remove_streamer(self, streamer):
        streamer = streamer.lower()
        if streamer in self.streamers.keys():
            self.streamers.pop(streamer)
            return True, 'Removed ' + streamer + ' from watchlist.'
        elif streamer in self.watched_streamers.keys():
            watcher = self.watched_streamers[streamer]['watcher']
            watcher.quit()
            return True, 'Removed ' + streamer + ' from watchlist.'
        else:
            return False, 'Could not find ' + streamer + '. Already removed?'

    def start(self):
        if not self.started:
            self._check_streams()
            self.started = True
            return 'Daemon is started.'
        else:
            return 'Daemon is already running.'

    def set_interval(self, secs):
        if secs < 1:
            secs = 1
        self.check_interval = secs
        return 'Interval is now set to ' + str(secs) + ' seconds.'

    def set_download_folder(self, download_folder):
        self.download_folder = download_folder
        return 'Download folder is now set to \'' + download_folder + '\' .'

    def _check_streams(self):
        user_ids = []

        # get channel ids of all streamers
        for streamer in self.streamers.keys():
            user_ids.append(self.streamers[streamer]['user_info']['id'])

        if user_ids:
            streams_info = twitch.get_stream_info(*user_ids)

            # save streaming information for all streamers, if it exists
            for stream_info in streams_info:
                streamer_name = stream_info['user_name'].lower()
                self.streamers[streamer_name].update({'stream_info': stream_info})

            live_streamers = []

            # check which streamers are live
            for streamer_info in self.streamers.values():
                try:
                    stream_info = streamer_info['stream_info']
                    if stream_info['type'] == 'live':
                        live_streamers.append(stream_info['user_name'].lower())
                except KeyError:
                    pass

            self._start_watchers(live_streamers)

        if not self.kill:
            t = threading.Timer(self.check_interval, self._check_streams)
            t.start()

    def _start_watchers(self, live_streamers_list):
        for live_streamer in live_streamers_list:
            if live_streamer not in self.watched_streamers:
                live_streamer_dict = self.streamers.pop(live_streamer)
                curr_watcher = Watcher(live_streamer_dict, self.download_folder)
                self.watched_streamers.update({live_streamer: {'watcher': curr_watcher,
                                                               'streamer_dict': live_streamer_dict}})
                if not self.kill:
                    t = self.pool.submit(curr_watcher.watch)
                    t.add_done_callback(self._watcher_callback)

    def _watcher_callback(self, returned_watcher):
        streamer_dict = returned_watcher.result()
        streamer = streamer_dict['user_info']['login']
        kill = streamer_dict['kill']
        cleanup = streamer_dict['cleanup']
        self.watched_streamers.pop(streamer)
        if not cleanup:
            print('Finished watching ' + streamer)
        else:
            output_filepath = streamer_dict['output_filepath']
            if os.path.exists(output_filepath):
                os.remove(output_filepath)
        if not kill:
            self.add_streamer(streamer, streamer_dict['preferred_quality'])

    def get_streamers(self):
        return list(self.watched_streamers.keys()), list(self.streamers.keys())

    def exit(self):
        self.kill = True
        for streamer in self.watched_streamers.values():
            watcher = streamer['watcher']
            watcher.quit()
        self.pool.shutdown()
        self.server_close()
        threading.Thread(target=self.shutdown, daemon=True).start()
        return 'Daemon exited successfully'


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    server = Daemon(('127.0.0.1', 1234), ATRHandler.ATRHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.exit()

    print('exited gracefully')

import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from http.server import HTTPServer

import requests
from pyngrok import ngrok
from twitch import TwitchClient, constants as tc_const

import ATRHandler
from utils import get_client_id, StreamQualities
from watcher import Watcher


class Daemon(HTTPServer):
    #
    # CONSTANTS
    #
    VALID_BROADCAST = ['live']  # 'rerun' can be added through commandline flags/options
    WEBHOOK_SECRET = 'automaticTwitchRecorder'
    WEBHOOK_URL_PREFIX = 'https://api.twitch.tv/helix/streams?user_id='
    PORT = 1234
    LEASE_SECONDS = 864000  # 10 days = 864000

    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.streamers = {}
        self.watched_streamers = {}
        self.client_id = get_client_id()
        self.twitch_client = TwitchClient(client_id=self.client_id)
        self.ngrok_url = ngrok.connect(port=self.PORT)
        self.kill = False
        self.started = False
        # ThreadPoolExecutor(max_workers): If max_workers is None or not given, it will default to the number of
        # processors on the machine, multiplied by 5
        self.pool = ThreadPoolExecutor()

    def add_streamer(self, streamer, quality=StreamQualities.BEST.value):
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
            user_info = self.twitch_client.users.translate_usernames_to_ids(streamer)

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

    def _check_streams(self):
        user_ids = []

        # TEST WORKAROUND: check if watched streamers are hosting
        # for streamer in self.watched_streamers.keys():
        #     watched_streamer = self.watched_streamers[streamer]
        #     watched_streamer_id = watched_streamer['streamer_dict']['user_info']['id']
        #     watched_streamer_stream_info = \
        #         self.twitch_client.streams.get_stream_by_user(watched_streamer_id,
        #                                                       stream_type=tc_const.STREAM_TYPE_LIVE)
        #     if not watched_streamer_stream_info:
        #         watched_streamer['watcher'].clean_break()

        # get channel ids of all streamers
        for streamer in self.streamers.keys():
            user_ids.append(self.streamers[streamer]['user_info']['id'])

        # better, but unreliable for some streams
        # e.g. Nani was playing unlisted game 'King of Retail' and it did not show up
        # streams_info = self.CLIENT.streams.get_live_streams(user_ids, tc_const.STREAM_TYPE_ALL)

        streams_info = []

        for user_id in user_ids:
            # register webhooks
            self._post_webhook_request(user_id)

            # TODO: might change STREAM_TYPE in a later version?!
            # request stream information for each channel id, response may be None
            response = self.twitch_client.streams.get_stream_by_user(user_id, stream_type=tc_const.STREAM_TYPE_LIVE)
            streams_info.append(response)

        # save streaming information for all streamers, if it exists
        for stream_info in streams_info:
            if stream_info:
                streamer_name = stream_info['channel']['name']
                self.streamers[streamer_name].update({'stream_info': stream_info})

        live_streamers = []

        # check which streamers are live
        for streamer_info in self.streamers.values():
            try:
                stream_info = streamer_info['stream_info']

                if stream_info['broadcast_platform'] == tc_const.STREAM_TYPE_LIVE:
                    live_streamers.append(stream_info['channel']['name'])
                    # live_streamers.append(stream_info['channel']['display_name']) # TODO: any differences?
            except KeyError:
                pass

        self._start_watchers(live_streamers)

    def _start_watchers(self, live_streamers_list):
        for live_streamer in live_streamers_list:
            if live_streamer not in self.watched_streamers:
                live_streamer_dict = self.streamers.pop(live_streamer)
                curr_watcher = Watcher(live_streamer_dict)
                self.watched_streamers.update({live_streamer: {'watcher': curr_watcher,
                                                               'streamer_dict': live_streamer_dict}})

    def _watcher_callback(self, returned_watcher):
        streamer_dict = returned_watcher.result()
        streamer = streamer_dict['user_info']['name']
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

    def _post_webhook_request(self, user_id):
        payload = {'hub.mode': 'subscribe',
                   'hub.topic': self.WEBHOOK_URL_PREFIX + user_id,
                   'hub.callback': self.ngrok_url,
                   'hub.lease_seconds': self.LEASE_SECONDS,
                   'hub.secret': self.WEBHOOK_SECRET
                   }
        auth = {'Client-ID': str(get_client_id())}
        print('posting REQUEST, DATA: ' + str(payload))
        requests.post('https://api.twitch.tv/helix/webhooks/hub', data=payload, headers=auth)

    # def verify_request(self, request, client_address):
    #     print('verify_request', request, client_address)
    #     return socketserver.TCPServer.verify_request(self, request, client_address)
    #
    # def process_request(self, request, client_address):
    #     print('process_request', request, client_address)
    #     return socketserver.TCPServer.process_request(self, request, client_address)
    #
    # def finish_request(self, request, client_address):
    #     print('finish_request', request, client_address)
    #     return socketserver.TCPServer.finish_request(self, request, client_address)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    server = Daemon(('127.0.0.1', 8924), ATRHandler.ATRHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.exit()

    # myDaemon = get_instance()
    # myDaemon.add_streamer('forsen')
    # myDaemon.add_streamer('nani')
    # myDaemon.add_streamer('nymn')
    # myDaemon.add_streamer('bobross')
    # myDaemon.start()
    # myDaemon.get_streamers()
    print('exited gracefully')

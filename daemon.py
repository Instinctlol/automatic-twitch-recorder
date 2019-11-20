import hmac
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
from urllib.parse import urlparse

import requests
from pyngrok import ngrok
from twitch import TwitchClient, constants as tc_const

from utils import get_client_id, StreamQualities
from watcher import Watcher
from events import TwitchStreamUpdate


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
        self.check_interval = 30
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
        qualities = [q.value for q in StreamQualities]
        if quality not in qualities:
            print('Invalid quality: ' + quality + '.')
            print('Quality options: ' + str(qualities))
        else:
            streamer_dict.update({'preferred_quality': quality})

            # get channel id of streamer
            user_info = self.twitch_client.users.translate_usernames_to_ids(streamer)

            # check if user exists
            if user_info:
                streamer_dict.update({'user_info': user_info[0]})
                self.streamers.update({streamer: streamer_dict})
                print('Successfully added ' + streamer + ' to watchlist.')
            else:
                print('Invalid streamer name: ' + streamer + '.')

    def remove_streamer(self, streamer):
        # TODO: frickly. What if we are currently checking if streamer is online and we're removing it at the same time?
        if streamer in self.streamers.keys():
            self.streamers.pop(streamer)
            print('Removed ' + streamer + ' from watchlist.')
        elif streamer in self.watched_streamers.keys():
            watcher = self.watched_streamers[streamer]['watcher']
            watcher.quit()
            print('Removed ' + streamer + ' from watchlist.')
        else:
            print('Could not find ' + streamer + '. Already removed?')

    def start(self):
        if not self.started:
            print('Daemon is started. Will check every ' + str(self.check_interval) + ' seconds.')
            self._watch_streams()
        else:
            print('Daemon is already running.')

    def _watch_streams(self):
        user_ids = []

        # TEST WORKAROUND: check if watched streamers are hosting
        for streamer in self.watched_streamers.keys():
            watched_streamer = self.watched_streamers[streamer]
            watched_streamer_id = watched_streamer['streamer_dict']['user_info']['id']
            watched_streamer_stream_info = \
                self.twitch_client.streams.get_stream_by_user(watched_streamer_id,
                                                              stream_type=tc_const.STREAM_TYPE_LIVE)
            if not watched_streamer_stream_info:
                watched_streamer['watcher'].clean_break()

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

    def handle_twitch_stream_update_event(self, twitchstreamupdateevent):
        print("HANDLE_TWITCH_STREAM_UPDATE: " + twitchstreamupdateevent.body)
        print('abc')

    def _start_watchers(self, live_streamers_list):
        for live_streamer in live_streamers_list:
            if live_streamer not in self.watched_streamers:
                live_streamer_dict = self.streamers.pop(live_streamer)
                curr_watcher = Watcher(live_streamer_dict)
                self.watched_streamers.update({live_streamer: {'watcher': curr_watcher,
                                                               'streamer_dict': live_streamer_dict}})
                # if not self.kill:
                #     t = self.pool.submit(curr_watcher.watch)
                #     t.add_done_callback(self._watcher_callback)

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


class _ATRHandler(BaseHTTPRequestHandler):
    daemon = None

    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)
        self.daemon = server

    def _set_response(self):
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    # send challenge back to twitch
    def do_GET(self):
        query = urlparse(self.path).query
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        # self.daemon.handle_twitch_stream_update_event(TwitchStreamUpdate("GET REQUEST:" + str(self.headers)))
        try:
            query_components = dict(qc.split("=") for qc in query.split("&"))
            challenge = query_components["hub.challenge"]
            # s = ''.join(x for x in challenge if x.isdigit())
            # print(s)
            # print(challenge)
            self.send_response(HTTPStatus.OK)
            self.end_headers()
            self.wfile.write(bytes(challenge, "utf-8"))
        except:
            query_components = None
            challenge = None
            self._set_response()
            self.wfile.write(bytes("Hello Stranger :)", "utf-8"))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length).decode()  # <--- Gets the data itself
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                     str(self.path), str(self.headers), post_data)

        if self.path == '/cmd/':
            logging.info('successful cmd!')
            self._set_response()
            self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))
        else:
            # self.daemon.handle_twitch_stream_update_event(TwitchStreamUpdate(post_data.decode('utf-8')))
            if 'Content-Type' in self.headers:
                content_type = str(self.headers['Content-Type'])
            else:
                raise ValueError("not all headers supplied.")
            if 'X-Hub-Signature' in self.headers:
                hub_signature = str(self.headers['X-Hub-Signature'])
                algorithm, hashval = hub_signature.split('=')
                print(hashval)
                print(algorithm)
                if post_data and algorithm and hashval:
                    gg = hmac.new(Daemon.WEBHOOK_SECRET.encode(), post_data, algorithm)
                    if not hmac.compare_digest(hashval.encode(), gg.hexdigest().encode()):
                        raise ConnectionError("Hash missmatch.")
            else:
                raise ValueError("not all headers supplied.")
            self._set_response()
            self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    server = Daemon(('127.0.0.1', 8921), _ATRHandler)
    server.add_streamer('forsen')
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

from watcher import Watcher
from concurrent.futures import ThreadPoolExecutor
from twitch import TwitchClient, constants as tc_const
from utils import get_client_id, StreamQualities
import threading
import time
import os


class Daemon:
    # immutable variables
    VALID_BROADCAST = ['live']  # 'rerun' can be added through commandline flags/options
    CLIENT = None
    # If max_workers is None or not given, it will default to the number of processors on the machine, multiplied by 5
    POOL = ThreadPoolExecutor()

    # mutable variables
    streamers = {}
    watched_streamers = {}
    check_interval = 30
    watch_quality = StreamQualities.BEST.value
    kill = False
    started = False

    def __init__(self):
        client_id = get_client_id()
        self.CLIENT = TwitchClient(client_id=client_id)

    def add_streamer(self, streamer, quality=watch_quality):
        streamer_dict = {}
        qualities = [q.value for q in StreamQualities]
        if quality not in qualities:
            print('Invalid quality: ' + quality + '.')
            print('Quality options: ' + str(qualities))
        else:
            streamer_dict.update({'preferred_quality': quality})

            # get channel id of streamer
            user_info = self.CLIENT.users.translate_usernames_to_ids(streamer)

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
            t = threading.Thread(target=self._watch_streams_loop)
            t.start()
        else:
            print('Daemon is already running.')

    def _watch_streams_loop(self):
        while self.kill is False:
            try:
                self._watch_streams()
            except Exception as e:
                print('Daemon crashed: ' + str(e))
                try:
                    client_id = get_client_id()
                    self.CLIENT = TwitchClient(client_id=client_id)
                    print('Daemon recovered success.')
                except Exception as e:
                    print('Daemon retry error.')
            time.sleep(self.check_interval)

    def _watch_streams(self):
        channel_ids = []

        # TEST WORKAROUND: check if watched streamers are hosting
        for streamer in self.watched_streamers.keys():
            watched_streamer = self.watched_streamers[streamer]
            watched_streamer_id = watched_streamer['streamer_dict']['user_info']['id']
            watched_streamer_stream_info = \
                self.CLIENT.streams.get_stream_by_user(watched_streamer_id, stream_type=tc_const.STREAM_TYPE_LIVE)
            if not watched_streamer_stream_info:
                watched_streamer['watcher'].clean_break()

        # get channel ids of all streamers
        for streamer in self.streamers.keys():
            channel_ids.append(self.streamers[streamer]['user_info']['id'])

        # better, but unreliable for some streams
        # e.g. Nani was playing unlisted game 'King of Retail' and it did not show up
        # streams_info = self.CLIENT.streams.get_live_streams(channel_ids, tc_const.STREAM_TYPE_ALL)

        streams_info = []

        # request stream information for each channel id, response may be None
        for channel_id in channel_ids:
            # TODO: might change STREAM_TYPE in a later version?!
            streams_info.append(
                self.CLIENT.streams.get_stream_by_user(channel_id, stream_type=tc_const.STREAM_TYPE_LIVE))

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

        # start a watcher for every live streamer and reschedule _watch_streams()
        for live_streamer in live_streamers:
            live_streamer_dict = self.streamers.pop(live_streamer)
            curr_watcher = Watcher(live_streamer_dict)
            self.watched_streamers.update({live_streamer: {'watcher': curr_watcher,
                                                           'streamer_dict': live_streamer_dict}})
            if not self.kill:
                t = self.POOL.submit(curr_watcher.watch)
                t.add_done_callback(self._watcher_callback)

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
        self.POOL.shutdown()


if __name__ == '__main__':
    myDaemon = Daemon()
    myDaemon.add_streamer('forsen')
    myDaemon.add_streamer('nani')
    myDaemon.add_streamer('nymn')
    myDaemon.add_streamer('bobross')
    myDaemon.start()
    myDaemon.get_streamers()
    print('abc')

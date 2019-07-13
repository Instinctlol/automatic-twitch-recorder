import datetime
import re
import subprocess
import sys
import os
import getopt
from requests import exceptions as reqexc
from threading import Timer
from twitch import TwitchClient
from twitch import constants as tc_const
import utils
from pathlib import Path
import streamlink
import streamlink.stream.hls

from enum import Enum


class StreamerStatus(Enum):
    ONLINE = 0
    OFFLINE = 1
    NOT_FOUND = 2
    ERROR = 3


class Daemon:
    # immutable variables
    VALID_BROADCAST = ['live']  # 'rerun' can be added through commandline flags/options
    CLIENT = None

    # mutable variables
    streamers = {}

    def __init__(self):
        client_id = utils.get_client_id()
        self.CLIENT = TwitchClient(client_id=client_id)

    def add_streamer(self, streamer):
        # get channel id of streamer
        user_info = self.CLIENT.users.translate_usernames_to_ids(streamer)

        if user_info:
            streamer_dict = {}
            streamer_dict.update({'user_info': user_info[0]})

            self.streamers.update({streamer: streamer_dict})
        else:
            print('invalid streamer name: ' + streamer)

    def check_streamers(self):
        channel_ids = []
        streamer_list = []

        for streamer in self.streamers.keys():
            channel_ids.append(self.streamers[streamer]['user_info']['id'])
            streamer_list.append(streamer)

        # better, but unreliable for some streams
        # e.g. Nani was playing unlisted game 'King of Retail' and it did not show up
        # streams_info = self.CLIENT.streams.get_live_streams(channel_ids, tc_const.STREAM_TYPE_ALL)

        streams_info = []

        for channel_id in channel_ids:
            # TODO: might change STREAM_TYPE in a later version?!
            streams_info.append(
                self.CLIENT.streams.get_stream_by_user(channel_id, stream_type=tc_const.STREAM_TYPE_LIVE))

        for stream_info in streams_info:
            if stream_info:
                streamer_name = stream_info['channel']['name']
                self.streamers[streamer_name].update({'stream_info': stream_info})

    # def loopcheck():
    #     status, stream_info = check_user(user)
    #     if status == 2:
    #         print('Username not found. Invalid username?')
    #         sys.exit(3)
    #     elif status == 3:
    #         print('Unexpected error. Maybe try again later')
    #     elif status == 1:
    #         t = Timer(time, loopcheck)
    #         print(user, 'is currently offline, checking again in', time, 'seconds')
    #         t.start()
    #     elif status == 0:
    #         print(user, 'is online. Stop.')
    #         filename = datetime.datetime.now().strftime('%Y-%m-%d %H.%M.%S') + ' - ' + user + ' - ' + re.sub(
    #             r'[^a-zA-Z0-9]+', ' ', stream_info['channel']['status']) + '.flv'
    #         dir = os.getcwd() + os.path.sep + user
    #         if not os.path.exists(dir):
    #             os.makedirs(dir)
    #         subprocess.call(['streamlink', 'https://twitch.tv/' + user, quality, '-o', filename], cwd=dir)
    #         print('Stream is done. Going back to checking..')
    #         t = Timer(time, loopcheck)
    #         t.start()

    def start(self):
        self.check_streamers()

        live_streamers = []

        for streamer_info in self.streamers.values():
            try:
                stream_info = streamer_info['stream_info']

                if stream_info['broadcast_platform'] == tc_const.STREAM_TYPE_LIVE:
                    live_streamers.append(stream_info['channel']['name'])
                    # live_streamers.append(stream_info['channel']['display_name']) # TODO: any differences?
            except KeyError:
                pass

        file_name = datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S")+" - "+live_streamers[0]+\
                    " - "+re.sub(r"[^a-zA-Z0-9]+", ' ',
                                 self.streamers[live_streamers[0]]['stream_info']['channel']['status'])+".flv"
        dir = os.getcwd() + os.path.sep + live_streamers[0] + os.path.sep
        if not os.path.exists(dir):
            os.makedirs(dir)
        streams = streamlink.streams(self.streamers[live_streamers[0]]['stream_info']['channel']['url'])

        best_stream = streams['best']
        record = True

        try:
            out_file = open(dir + file_name, "wb")  # open for [w]riting as [b]inary
            fd = best_stream.open()
            while record:
                data = fd.read(1024)
                out_file.write(data)
        except streamlink.StreamError:
            record = False
            out_file.close()
            fd.close()

        print('abc')


if __name__ == '__main__':
    myDaemon = Daemon()
    myDaemon.add_streamer('forsen')
    myDaemon.add_streamer('nani')
    myDaemon.add_streamer('nymn')
    myDaemon.add_streamer('singsing')
    myDaemon.start()
    print('abc')

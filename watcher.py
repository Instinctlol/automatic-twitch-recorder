import datetime
import sys

import streamlink
import os
from utils import get_valid_filename, StreamQualities


class Watcher:
    streamer_dict = {}
    streamer = ''
    stream_title = ''
    stream_quality = ''
    kill = False

    def __init__(self, streamer_dict):
        self.streamer_dict = streamer_dict
        self.streamer = self.streamer_dict['user_info']['name']
        self.stream_title = self.streamer_dict['stream_info']['channel']['status']
        # self.streamer = self.streamer_dict['display_name'] # TODO: any differences?
        self.stream_quality = self.streamer_dict['preferred_quality']

    def quit(self):
        self.kill = True

    def watch(self):
        curr_time = datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S")
        file_name = curr_time + " - " + self.streamer + " - " + get_valid_filename(self.stream_title) + ".flv"
        dir = os.getcwd() + os.path.sep + self.streamer + os.path.sep
        if not os.path.exists(dir):
            os.makedirs(dir)

        streams = streamlink.streams(self.streamer_dict['stream_info']['channel']['url'])
        try:
            stream = streams[self.stream_quality]
        except KeyError:
            print('Invalid stream quality: ' + self.stream_quality)
            print('Falling back to default case: best')
            self.stream_quality = StreamQualities.BEST.value
            self.streamer_dict['preferred_quality'] = self.stream_quality
            stream = streams[self.stream_quality]

        print(self.streamer + ' is live. Saving stream in ' +
              self.stream_quality + ' quality to ' + dir + file_name + '.')

        try:
            with open(dir + file_name, "ab") as out_file:  # open for [a]ppending as [b]inary
                fd = stream.open()

                while not self.kill:
                    data = fd.read(1024)

                    # If data is empty it's the end of stream
                    if not data:
                        fd.close()
                        out_file.close()
                        break

                    out_file.write(data)
        except streamlink.StreamError as err:
            print('StreamError: {0}'.format(err))  # TODO: test when this happens
        except IOError as err:
            # If file validation fails this error gets triggered.
            print('Failed to write data to file: {0}'.format(err))
        self.streamer_dict.update({'kill': self.kill})
        return self.streamer_dict

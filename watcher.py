import datetime
import streamlink
import os
from utils import get_valid_filename, StreamQualities


class Watcher:
    streamer_dict = {}
    streamer = ''
    stream_title = ''
    stream_quality = ''
    kill = False
    cleanup = False

    def __init__(self, streamer_dict):
        self.streamer_dict = streamer_dict
        self.streamer = self.streamer_dict['user_info']['name']
        self.stream_title = self.streamer_dict['stream_info']['channel']['status']
        # self.streamer = self.streamer_dict['display_name'] # TODO: any differences?
        self.stream_quality = self.streamer_dict['preferred_quality']

    def quit(self):
        self.kill = True

    def clean_break(self):
        self.cleanup = True

    def watch(self):
        curr_time = datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S")
        file_name = curr_time + " - " + self.streamer + " - " + get_valid_filename(self.stream_title) + ".ts"
        dir = os.getcwd() + os.path.sep + self.streamer + os.path.sep
        if not os.path.exists(dir):
            os.makedirs(dir)
        output_filepath = dir + file_name
        self.streamer_dict.update({'output_filepath': output_filepath})

        streams = streamlink.streams(self.streamer_dict['stream_info']['channel']['url'])
        try:
            stream = streams[self.stream_quality]
        except KeyError:
            temp_quality = self.stream_quality
            if len(streams) > 0:  # False => stream is probably offline
                if self.stream_quality in streams.keys():
                    self.stream_quality = StreamQualities.BEST.value
                else:
                    self.stream_quality = list(streams.keys())[-1]  # best not in streams? choose best effort quality
            else:
                self.kill = True

            if not self.kill:
                print('Invalid stream quality: ' + '\'' + temp_quality + '\'')
                print('Falling back to default case: ' + self.stream_quality)
                self.streamer_dict['preferred_quality'] = self.stream_quality
                stream = streams[self.stream_quality]
            else:
                stream = None

        if not self.kill and not self.cleanup and stream:
            print(self.streamer + ' is live. Saving stream in ' +
                  self.stream_quality + ' quality to ' + output_filepath + '.')

            try:
                with open(output_filepath, "ab") as out_file:  # open for [a]ppending as [b]inary
                    fd = stream.open()

                    while not self.kill and not self.cleanup:
                        data = fd.read(1024)

                        # If data is empty the stream has ended
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
            self.streamer_dict.update({'cleanup': self.cleanup})
            return self.streamer_dict

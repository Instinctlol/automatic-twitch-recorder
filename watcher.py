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
        self.streamer = self.streamer_dict['user_info']['display_name']
        self.streamer_login = self.streamer_dict['user_info']['login']
        self.stream_title = self.streamer_dict['stream_info']['title']
        self.stream_quality = self.streamer_dict['preferred_quality']

    def quit(self):
        self.kill = True

    def clean_break(self):
        self.cleanup = True

    def watch(self):
        curr_time = datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S")
        file_name = curr_time + " - " + self.streamer + " - " + get_valid_filename(self.stream_title) + ".ts"
        directory = os.getcwd() + os.path.sep + self.streamer_login + os.path.sep
        if not os.path.exists(directory):
            os.makedirs(directory)
        output_filepath = directory + file_name
        self.streamer_dict.update({'output_filepath': output_filepath})

        streams = streamlink.streams('https://www.twitch.tv/' + self.streamer_login)
        # Occurs when already recording another stream and new streamer (that is already live) is added
        # not sure why this error is thrown..
        # Traceback (most recent call last):
        #   File "C:\Program Files\Python36\lib\threading.py", line 916, in _bootstrap_inner
        #     self.run()
        #   File "E:\Downloads\automatic-twitch-recorder\venv\lib\site-packages\streamlink\stream\segmented.py", line 59, in run
        #     for segment in self.iter_segments():
        #   File "E:\Downloads\automatic-twitch-recorder\venv\lib\site-packages\streamlink\stream\hls.py", line 307, in iter_segments
        #     self.reload_playlist()
        #   File "E:\Downloads\automatic-twitch-recorder\venv\lib\site-packages\streamlink\stream\hls.py", line 235, in reload_playlist
        #     self.process_sequences(playlist, sequences)
        #   File "E:\Downloads\automatic-twitch-recorder\venv\lib\site-packages\streamlink\plugins\twitch.py", line 210, in process_sequences
        #     return super(TwitchHLSStreamWorker, self).process_sequences(playlist, sequences)
        # TypeError: super(type, obj): obj must be an instance or subtype of type
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
                self.cleanup = True

            if not self.cleanup:
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

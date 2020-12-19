import threading
import os
import time

import requests

import automatic_twitch_recorder.ATRHandler
from automatic_twitch_recorder.daemon import Daemon
from automatic_twitch_recorder.utils import read_config_from_env, get_safe_from_list

class DockerRunner:
    def start_internal_server(self):
        server = Daemon(('127.0.0.1', 1234), automatic_twitch_recorder.ATRHandler.ATRHandler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        return thread

    def init_server(self):
        self._set_interval_time()
        self._set_download_folder()
        self._add_multiple_streams()
        self._start_recording()

    def _set_interval_time(self):
        time = get_safe_from_list(os.environ, 'CHECK_INTERVAL')
        if not time:
            return
        
        payload = self._create_payload('time', time)
        self._send_cmd(payload)

    def _set_download_folder(self):
        download_folder = self._get_download_folder()
        payload = self._create_payload('download_folder', download_folder)
        self._send_cmd(payload)
    
    def _get_download_folder(self):
        download_folder =get_safe_from_list(os.environ, 'DOWNLOAD_FOLDER')
        if not download_folder:
            return '/recordings/#streamer#'
        
        return '/recordings/' + download_folder.strip('/')

    def _add_multiple_streams(self):
        streamers = self._get_streamers()
        for streamer in streamers:
            if streamer['quality']:
                payload = self._create_payload('add', streamer['name'], streamer['quality'])
            else:
                payload = self._create_payload('add', streamer['name'])

            self._send_cmd(payload)

    def _get_streamers(self):
        streamers_raw = get_safe_from_list(os.environ, 'STREAMERS')
        if not streamers_raw:
            return []
        
        streamers = []
        for settings_raw in streamers_raw.split('|'):
            settings = settings_raw.split('@')
            streamers.append({
                'name': settings[0],
                'quality': get_safe_from_list(settings, 1)
            })

        return streamers

    def _start_recording(self):
        payload = self._create_payload('start')
        self._send_cmd(payload)

    def _send_cmd(self, cmd_payload):
        r = requests.post('http://127.0.0.1:1234/cmd/', json=cmd_payload)
        resp_json = r.json()
        resp_ok = r.ok
        print(resp_json.pop('println'))
        return resp_ok, resp_json

    def _create_payload(self, command, *args):
        payload = {
            'cmd': command,
            'args': list(args)
        }
        return payload

if __name__ == '__main__':
    runner = DockerRunner()
    try:
        read_config_from_env()
        thread = runner.start_internal_server()
        runner.init_server()

        thread.join()
    except Exception as e:
        print(e)

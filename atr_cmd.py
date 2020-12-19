import cmd
import sys

import requests


# TODO: https://stackoverflow.com/questions/37866403/python-cmd-module-resume-prompt-after-async-event
class AtrCmd(cmd.Cmd):

    def _send_cmd(self, cmd_payload):
        r = requests.post('http://127.0.0.1:1234/cmd/', json=cmd_payload)
        resp_json = r.json()
        resp_ok = r.ok
        print(resp_json.pop('println'))
        return resp_ok, resp_json

    def _create_payload(self, command, *args):
        payload = {'cmd': command,
                   'args': list(args)
                   }
        return payload

    def __init__(self):
        super().__init__()

    def do_add(self, line):
        line = line.split(' ')
        payload = self._create_payload('add', *line)
        self._send_cmd(payload)

    def help_add(self):
        print('\n'.join([
            'add streamer [quality]',
            'Adds streamer to watchlist with (optional) selected quality.',
            'Default quality: best',
        ]))

    def do_remove(self, line):
        payload = self._create_payload('remove', line)
        self._send_cmd(payload)

    def help_remove(self):
        print('\n'.join([
            'remove streamer',
            'Removes streamer from watchlist, also stops recording if currently recording streamer.',
        ]))

    def do_list(self, line):
        payload = self._create_payload('list')
        self._send_cmd(payload)

    def help_list(self):
        print('\n'.join([
            'list',
            'List all watched streamers, seperated in offline and live sets.',
        ]))

    def do_start(self, line):
        payload = self._create_payload('start')
        self._send_cmd(payload)

    def help_start(self):
        print('\n'.join([
            'start',
            'Starts the configured daemon. You may still configure it further while it is running.',
        ]))

    def do_time(self, line):
        try:
            payload = self._create_payload('time', line)
            self._send_cmd(payload)
        except ValueError:
            print('\''+line+'\' is not valid.')

    def help_time(self):
        print('\n'.join([
            'time seconds',
            'Configures the check interval in seconds.',
            'It\'s advised not to make it too low and to stay above 10 seconds.',
            'Default check interval: 30 seconds.',
        ]))

    def do_download_folder(self, line):
        payload = self._create_payload('download_folder', line)
        self._send_cmd(payload)

    def help_download_folder(self):
        print('\n'.join([
            'download_folder path',
            'Configures the download folder for saving the videos.',
        ]))

    def do_EOF(self, line):
        self.do_exit(line)
        return True

    def do_exit(self, line):
        payload = self._create_payload('exit')
        self._send_cmd(payload)
        sys.exit()

    def help_exit(self):
        print('\n'.join([
            'exit',
            'Exits the application, stopping all running recording tasks.',
        ]))

    def cmdloop_with_keyboard_interrupt(self):
        try:
            self.cmdloop()
        except KeyboardInterrupt:
            self.do_exit('')


if __name__ == '__main__':
    AtrCmd().cmdloop_with_keyboard_interrupt()

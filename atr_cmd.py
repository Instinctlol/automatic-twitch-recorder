import cmd
import sys
from daemon import Daemon


# TODO: https://stackoverflow.com/questions/37866403/python-cmd-module-resume-prompt-after-async-event
class AtrCmd(cmd.Cmd):

    daemon = None

    def __init__(self):
        self.daemon = Daemon()
        super().__init__()

    def do_add(self, line):
        line = line.split(' ')
        if len(line) > 1:
            self.daemon.add_streamer(line[0], line[1])
        else:
            self.daemon.add_streamer(line[0])

    def help_add(self):
        print('\n'.join([
            'add streamer [quality]',
            'Adds streamer to watchlist with (optional) selected quality.',
            'Default quality: best',
        ]))

    def do_remove(self, line):
        self.daemon.remove_streamer(line)

    def help_remove(self):
        print('\n'.join([
            'remove streamer',
            'Removes streamer from watchlist, also stops recording if currently recording streamer.',
        ]))

    def do_list(self, line):
        live, offline = self.daemon.get_streamers()
        print('Live: ' + str(live))
        print('Offline: ' + str(offline))

    def help_list(self):
        print('\n'.join([
            'list',
            'List all watched streamers, seperated in offline and live sets.',
        ]))

    def do_start(self, line):
        self.daemon.start()

    def help_start(self):
        print('\n'.join([
            'start',
            'Starts the configured daemon. You may still configure it further while it is running.',
        ]))

    def do_time(self, line):
        try:
            self.daemon.check_interval = int(line)
            print('Changed check interval to: ' + line + ' seconds.')
        except ValueError:
            print('\''+line+'\' is not valid.')

    def help_time(self):
        print('\n'.join([
            'time seconds',
            'Configures the check interval in seconds.',
            'Please do not make it too low and stay above 10 seconds.',
            'Default check interval: 30 seconds.',
        ]))

    def do_EOF(self, line):
        self.do_exit(line)
        return True

    def do_exit(self, line):
        print('exiting')
        self.daemon.exit()
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

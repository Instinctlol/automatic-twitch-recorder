# automatic-twitch-recorder

Checks if a user on twitch is currently streaming and then records the stream via streamlink

## Dependencies:

- streamlink (https://streamlink.github.io)
- python-twitch-client (https://github.com/tsifrer/python-twitch-client)
- python (https://www.python.org/)

## Installation:

- clone this repo or download
- make sure you have python3 installed
- open cmd/terminal
  - change directory into folder containing the file 'requirements.txt'
  - type `pip install -r requirements.txt`

## Usage:

### Using the CLI (Command-line interface)

- in your cmd/terminal, run `python atr_cmd.py`
- type `help`
  - `add streamer [quality]`: adds the streamer you want to record in given optional quality, e.g. `add forsen`. Default quality: `best`
  - `time 30`: sets check interval in seconds, please don't go below `10`
  - `remove streamer`: removes streamer, also stops recording this streamer
  - `start`: starts checking for / recording all added streamers
  - `list`: prints all added streamers
  - `exit`: stops the application and all currently running recordings


### Outdated:

check.py is not supported anymore, it's only included for legacy purposes and may be removed at a later point in time.

- ~~in your cmd/terminal, run `python check.py [options] [user]`~~
  - ~~[time] is measured in seconds, e.g. '30' for 30 seconds~~
  - ~~[user] is the user you want to record, e.g. 'forsen'~~
  - ~~[quality] is the stream quality you want to record, 'best' is default. Refer to [streamlink documentation](https://streamlink.github.io/) for more info.~~
- ~~call `python check.py --help` for a detailed description.~~


## Bugs:

- CLI shenanigans
    - text will get printed into the prompt / user input. However, your input will still be valid, so do not worry. This does not restrict the functionality of this application.
    - There's an open [stackoverflow question](https://stackoverflow.com/questions/57027294/cmd-module-async-job-prints-are-overwriting-prompt-input) for this. Any volunteers?

## Plans for the future:

- When done recording, upload to YouTube
- Export to .exe so you don't have to install python
  - PyInstaller and streamlink apparently do not work well together (streamlink will throw NoPluginError). Help is appreciated.
- Create a GUI with Qt (PyQt5 or PySide2) (fairly easy, but time consuming)

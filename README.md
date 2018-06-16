# automatic-twitch-recorder

Checks if a user on twitch is currently streaming and then records the stream via streamlink

## Dependencies:

- [streamlink](https://streamlink.github.io)
- [python-twitch-client](https://github.com/tsifrer/python-twitch-client)
- [python](https://www.python.org/)

## Installation:

- clone this repo or download
- make sure you have python3 installed
- open cmd/terminal
  - change directory into folder containing the file 'requirements.txt'
  - type `pip install -r requirements.txt`
- You will need your twitch client id
  - you can create it [here](https://glass.twitch.tv/console/apps)

## Usage:

- in your cmd/terminal, run `python check.py [options] [user]`
  - [time] is measured in seconds, e.g. '30' for 30 seconds
  - [user] is the user you want to record, e.g. 'forsen'
  - [quality] is the stream quality you want to record, 'best' is default. Refer to [streamlink documentation](https://streamlink.github.io/) for more info.
- call `python check.py --help` for a detailed description.


## Plans for the future:

- When done recording, upload to YouTube
- Monitor multiple streams / implement threading
- Export to .exe so you don't have to install python (very easy)
- Use streamlink objects rather than a subprocess

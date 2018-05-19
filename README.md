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
  - type 'pip install -r requirements.txt'
- edit line 9 in 'check.py' with your text editor of choice so it contains your twitch client id
  - you can create it [here](https://glass.twitch.tv/console/apps)

## Usage:

- in your cmd/terminal, type 'python check.py [time] [user] [quality]'
  - [time] is measured in seconds, e.g. '30' for 30 seconds
  - [user] is the user you want to record, e.g. 'forsen'
  - [quality] is the stream quality you want to record, 'best' is default. Refer to streamlink documentation for more info.
- e.g. 'python check.py 30 forsen best' will check every 30 seconds if forsen is online, if so: record with best quality.


## Plans for the future:

- When done recording, upload to YouTube

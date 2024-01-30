# discontinued

This script was declared end-of-life and is not maintained anymore. Please have a look into well maintained, more feature-rich solutions, like [ganymede](https://github.com/Zibbp/ganymede) and [LiveStreamDVR](https://github.com/MrBrax/LiveStreamDVR)

# automatic-twitch-recorder

Checks if a user on twitch is currently streaming and then records the stream via streamlink

## Dependencies:

- streamlink (https://streamlink.github.io)
- python3 (https://www.python.org/) (I use [python3.6](https://www.python.org/downloads/release/python-368/) for windows)

## Installation:

- clone this repo or download
- make sure you have python3 installed
- open cmd/terminal
  - change directory into folder containing the file 'requirements.txt'
  - type `pip install -r requirements.txt`

## Usage:

### Using the CLI (Command-line interface)

- in your cmd/terminal, run `python main.py`
- type `help`
  - `add streamer [quality]`: adds the streamer you want to record in given optional quality, e.g. `add forsen`. Default quality: `best`, quality options: `1080p60, 1080p, 720p60, 720p, 480p, 360p, 160p, audio_only`
  - `time 10`: sets check interval in seconds
  - `remove streamer`: removes streamer, also stops recording this streamer
  - `start`: starts checking for / recording all added streamers
  - `list`: prints all added streamers
  - `exit`: stops the application and all currently running recordings
  - `download_folder path`: sets the download folder for saving the recordings. (#streamer# will be replaced with the name of the streamer)

Example inputs to record forsen and nymn (this will also repeatedly check if they are online):

```
$ add forsen
$ add nymn
$ start
```


## Bugs:

- CLI shenanigans
    - text will get printed into the prompt / user input. However, your input will still be valid, so do not worry. This does not restrict the functionality of this application.
    - There's an open [stackoverflow question](https://stackoverflow.com/questions/57027294/cmd-module-async-job-prints-are-overwriting-prompt-input) for this. Any volunteers?

## Plans for the future:

- Refactor to easily support any supported streamlink platform, e.g. YouTube.
- When done recording, upload to YouTube
- Export to .exe so you don't have to install python
  - PyInstaller and streamlink apparently do not work well together (streamlink will throw NoPluginError). Help is appreciated.
- Create a GUI with Qt (PyQt5 or PySide2) (fairly easy, but time consuming)

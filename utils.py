import os
from enum import Enum
from pathlib import Path
from pathvalidate import sanitize_filename

CLIENT_ID_FILE = os.getcwd() + os.path.sep + 'client_id.txt'  # Location of client_id.txt config file.


# TODO: figure it out from streamlink library
class StreamQualities(Enum):
    AUDIO_ONLY = 'audio_only'
    _160p = '160p'
    _360 = '360p'
    _480p = '480p'
    _720p = '720p'
    _720p60 = '720p60'
    _1080p = '1080p'
    _1080p60 = '1080p60'
    WORST = 'worst'
    BEST = 'best'


def get_client_id():
    client_id_path = Path(CLIENT_ID_FILE)

    try:
        client_id_path.resolve(strict=True)
    except FileNotFoundError as ex:
        print(ex)
        print('Client id file doesn\'t exist.')
        print('Visit the following website to generate a client id for this script.')
        print('https://glass.twitch.tv/console/apps')
        print('Enter client id from website.')
        client_id = input('client id: ')
        client_file = open(client_id_path, 'w')
        client_file.write(client_id)
        client_file.close()
        return client_id
    else:
        client_file = open(client_id_path, 'r')
        client_id = client_file.read()
        client_file.close()
        return client_id


def get_valid_filename(s):
    s = str(s)
    return sanitize_filename(s)

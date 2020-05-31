import os
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import json

import requests
from pathvalidate import sanitize_filename

CONFIG_FILE = os.getcwd() + os.path.sep + 'config.txt'  # Location of config.txt config file.
_APP_ACCESS_TOKEN = ''
_APP_ACCESS_TOKEN_REFRESH_TIME = None
CONFIG = None


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


def _read_config():
    global CONFIG
    config_path = Path(CONFIG_FILE)
    try:
        config_path.resolve(strict=True)
    except FileNotFoundError as ex:
        config_file = open(config_path, 'w')
        CONFIG = {
            'client_id': '',
            'client_secret': '',
            'ngrok_authtoken': ''
        }
        config_file.write(json.dumps(CONFIG))
        config_file.close()
    else:
        config_file = open(config_path, 'r')
        CONFIG = json.loads(config_file.read())
        config_file.close()


def _write_config():
    global CONFIG
    config_path = Path(CONFIG_FILE)
    config_file = open(config_path, 'w')
    config_file.write(json.dumps(CONFIG))
    config_file.close()


def get_client_id():
    global CONFIG
    if not CONFIG:
        _read_config()
    if not CONFIG['client_id']:
        print('Client id unset.')
        print('Visit the following website to generate a client id and client secret for this script.')
        print('https://dev.twitch.tv/console/apps')
        print('Enter client id from website.')
        CONFIG['client_id'] = input('client id: ')
        print('Enter client secret from website.')
        CONFIG['client_secret'] = input('client secret: ')
        _write_config()
    return CONFIG['client_id']


def get_client_secret():
    global CONFIG
    if not CONFIG:
        _read_config()
    if not CONFIG['client_secret']:
        print('Client secret unset.')
        print('Visit the following website to get a client secret for this script.')
        print('https://dev.twitch.tv/console/apps')
        print('Enter client secret from website.')
        CONFIG['client_secret'] = input('client secret: ')
        _write_config()
    return CONFIG['client_secret']


def get_ngrok_auth_token():
    global CONFIG
    if not CONFIG:
        _read_config()
    if not CONFIG['ngrok_authtoken']:
        print('Ngrok authtoken unset.')
        print('Visit the following website to generate an authtoken for this script.')
        print('https://dashboard.ngrok.com/auth/your-authtoken')
        print('Enter authtoken from website.')
        CONFIG['ngrok_authtoken'] = input('Authtoken: ')
        _write_config()
    return CONFIG['ngrok_authtoken']


def get_app_access_token():
    global _APP_ACCESS_TOKEN, _APP_ACCESS_TOKEN_REFRESH_TIME
    # API Notes:
    # App access tokens and ID tokens cannot be refreshed.
    # No scopes are needed when requesting app access tokens.
    oauth_url = 'https://id.twitch.tv/oauth2/token?client_id={0}&client_secret={1}&grant_type=client_credentials'
    if not _APP_ACCESS_TOKEN or not _APP_ACCESS_TOKEN_REFRESH_TIME or _APP_ACCESS_TOKEN_REFRESH_TIME < datetime.now():
        r = requests.post(oauth_url.format(get_client_id(), get_client_secret()))

        # {
        #   "access_token": "<user access token>",
        #   "refresh_token": "",
        #   "expires_in": <number of seconds until the token expires>,
        #   "scope": ["<your previously listed scope(s)>"],
        #   "token_type": "bearer"
        # }

        oauth_json = r.json()
        _APP_ACCESS_TOKEN = oauth_json['access_token']
        _APP_ACCESS_TOKEN_REFRESH_TIME = datetime.now() + timedelta(seconds=oauth_json['expires_in'] - 60)
    return _APP_ACCESS_TOKEN


def get_valid_filename(s):
    s = str(s)
    return sanitize_filename(s)

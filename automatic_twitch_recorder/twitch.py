import requests

import automatic_twitch_recorder.utils

def get_twitch_auth() -> dict:
    return {
        'Client-ID': str(automatic_twitch_recorder.utils.get_client_id()),
        'Authorization': 'Bearer ' + automatic_twitch_recorder.utils.get_app_access_token()
    }

def get_user_info(user_login, *args: str) -> list:
    """
    Gets user info for user logins
    See https://dev.twitch.tv/docs/api/reference#get-users

    Parameters
    ----------
    user_login: str
        username string
    args: str
        additional string usernames (max. 99)

    Returns
    -------
    list
        contains user_info dicts
    """
    get_user_id_url = 'https://api.twitch.tv/helix/users?login=' + user_login
    if len(args) > 99:
        args = args[:99]
    for user_login_i in args:
        get_user_id_url += '&login=' + user_login_i
    r = requests.get(get_user_id_url, headers=get_twitch_auth())
    temp = r.json()
    if temp['data']:
        return list(temp['data'])
    else:
        return []


def get_stream_info(user_id: str, *args):
    """
    Gets stream info for user ids
    See https://dev.twitch.tv/docs/api/reference#get-streams

    Parameters
    ----------
    user_id: str
        user id string
    args: str
        additional string user ids (max. 99)

    Returns
    -------
    list
        contains stream_info dicts
    """
    if len(args) > 99:
        args = args[:99]
    get_user_id_url = 'https://api.twitch.tv/helix/streams?first=100&user_id=' + user_id
    for user_id in args:
        get_user_id_url += '&user_id=' + user_id
    r = requests.get(get_user_id_url, headers=get_twitch_auth())
    temp = r.json()
    if temp['data']:
        return list(temp['data'])
    else:
        return []

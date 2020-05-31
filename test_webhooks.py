from pyngrok import ngrok
import requests
import utils
import twitch

# payload = {'cmd': 'add',
#            'args': ['nymn']
#            }
# r = requests.post('http://127.0.0.1:8924/cmd/', json=payload)

auth = {'Client-ID': str(utils.get_client_id()),
        'Authorization': 'Bearer ' + utils.get_app_access_token()}


# def get_user_ids(user_logins):
#     get_user_id_url = 'https://api.twitch.tv/helix/users?login=' + user_logins[0]
#     for id in user_logins[1:]:
#         get_user_id_url += '&login='+id
#     r = requests.get(get_user_id_url, headers=auth)
#     return r.json()['data']
#
#
# get_user_ids(['nymn', 'forsen'])

# test = twitch.get_stream_info(['62300805', '22484632', '47627824'])
# offline -> not in response
# test = [{'id': '1797093073', 'user_id': '22484632', 'user_name': 'forsen', 'game_id': '509658', 'type': 'live', 'title': '@forsen, Games and shit!', 'viewer_count': 8819, 'started_at': '2020-05-31T13:56:18Z', 'language': 'en', 'thumbnail_url': 'https://static-cdn.jtvnw.net/previews-ttv/live_user_forsen-{width}x{height}.jpg', 'tag_ids': ['6ea6bca4-4712-4ab9-a906-e3336a9d8039']}, {'id': '1795861249', 'user_id': '62300805', 'user_name': 'NymN', 'game_id': '743', 'type': 'live', 'title': '5days to get good@chess -  movie night later :)))) | @nymnion on twitter/insta/youtube', 'viewer_count': 3967, 'started_at': '2020-05-31T11:49:26Z', 'language': 'en', 'thumbnail_url': 'https://static-cdn.jtvnw.net/previews-ttv/live_user_nymn-{width}x{height}.jpg', 'tag_ids': ['6ea6bca4-4712-4ab9-a906-e3336a9d8039']}, {'id': '1783598945', 'user_id': '47627824', 'user_name': 'RocketBeansTV', 'game_id': '417752', 'type': 'live', 'title': 'Das Kneipenquiz E07 ', 'viewer_count': 596, 'started_at': '2020-05-30T14:22:59Z', 'language': 'de', 'thumbnail_url': 'https://static-cdn.jtvnw.net/previews-ttv/live_user_rocketbeanstv-{width}x{height}.jpg', 'tag_ids': ['9166ad14-41f1-4b04-a3b8-c8eb838c6be6']}]

# rocketbeans https://api.twitch.tv/helix/streams?user_id=47627824
# forsen https://api.twitch.tv/helix/streams?user_id=22484632
# nani https://api.twitch.tv/helix/streams?user_id=93031467
# nymn https://api.twitch.tv/helix/streams?user_id=62300805
topic = "https://api.twitch.tv/helix/streams?user_id=4762782"
lease_seconds = 60 * 60

ngrok_url = 'http://e9645e34ef02.ngrok.io'  # ngrok.connect(port=1234) from Daemon, also shown in http://127.0.0.1:4040
secret = 'automaticTwitchRecorder'

payload = {'hub.mode': 'subscribe',
           'hub.topic': topic,
           'hub.callback': ngrok_url + '/webhooks/',
           'hub.lease_seconds': lease_seconds,
           'hub.secret': secret
           }
r = requests.post('https://api.twitch.tv/helix/webhooks/hub', data=payload, headers=auth)
print('abc')

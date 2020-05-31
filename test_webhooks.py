from pyngrok import ngrok
import requests
import utils

# payload = {'cmd': 'add',
#            'args': ['nymn']
#            }
# r = requests.post('http://127.0.0.1:8924/cmd/', json=payload)

# rocketbeans https://api.twitch.tv/helix/streams?user_id=47627824
# forsen https://api.twitch.tv/helix/streams?user_id=22484632
# nani https://api.twitch.tv/helix/streams?user_id=93031467
# nymn https://api.twitch.tv/helix/streams?user_id=62300805
topic = "https://api.twitch.tv/helix/streams?user_id=4762782"
auth = {'Client-ID': str(utils.get_client_id()),
        'Authorization': 'Bearer ' + utils.get_app_access_token()}
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

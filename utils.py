import os
from pathlib import Path

CLIENT_ID_FILE = os.getcwd() + os.path.sep + 'client_id.txt'  # Location of client_id.txt config file.


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

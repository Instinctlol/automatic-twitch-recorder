import sys
import os
from requests import exceptions as reqexc
from twitch import TwitchClient


CLIENT_ID=''
CLIENT_ID_FILE = os.getcwd()+os.path.sep+"client_id.txt"


def check_client_id():
    global CLIENT_ID
    try:
        client_file=open(CLIENT_ID_FILE,'r')
    except FileNotFoundError as ex:
        print(ex)
        print("Client id file doesn't exist.")
        get_client_id()
        sys.exit(4)
    CLIENT_ID=client_file.read()
    client_file.close()

def get_client_id():
    print("Visit the following website to generate a client id for this script.")
    print("https://glass.twitch.tv/console/apps")
    print("Enter client id from website.")
    id=input("client id: ")
    client_file=open(CLIENT_ID_FILE,'w')
    client_file.write(id)
    client_file.close()
    sys.exit(4)

class TwitchUser(object):
    """docstring for TwitchUser."""
    def __init__(self, user, **kwargs):
        super(TwitchUser, self).__init__()
        self.user = user
        self.quality = kwargs.get("quality","best")
        self.rerun = kwargs.get("rerun",False)
        self.time = kwargs.get("time",30)
        self.filename=None
        self.recdir=os.getcwd()+os.path.sep+self.user
        self.outdir=None
        self.broadcasts = ['live']
        if self.rerun:
            self.broadcasts.append('rerun')
        self.response = None
        if not self.valid_user():
            print("'%s' is not a valid user" %(self.user))

    def get_response(self):
        global CLIENT_ID
        try:
            self.client = TwitchClient(client_id=CLIENT_ID)
            self.response = self.client.users.translate_usernames_to_ids(self.user)
        except reqexc.HTTPError as ex:
            print("Bad client id: '%s'" %(CLIENT_ID))
            print(ex)
            get_client_id()
            sys.exit(4)

    def is_online(self):
        self.get_response()
        self.stream_info = None
        if self.valid_user():
            self.user_id = self.response[0].id
            self.stream_info = self.client.streams.get_stream_by_user(self.user_id)
        if self.stream_info is not None:
            if self.stream_info.broadcast_platform in self.broadcasts:
                return True
        return False


    def valid_user(self):
        if self.response is None:
            self.get_response()
        return not self.response.__len__() == 0

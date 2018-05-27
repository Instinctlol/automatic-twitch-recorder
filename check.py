#This script checks if a user on twitch is currently streaming and then records the stream via streamlink
from threading import Timer
import sys
import subprocess
import datetime
from twitch import TwitchClient
import re

CLIENT_ID = 'PASTE YOUR CLIENT ID HERE AS A STRING'
# e.g. CLIENT_ID = '123456789ABCDEFG'



def check_user(user):
    """ returns 0: online, 1: offline, 2: not found, 3: error """

    client = TwitchClient(client_id=CLIENT_ID)
    response = client.users.translate_usernames_to_ids(user)
    stream_info = 0
    if response.__len__() > 0:
        user_id = response[0].id
        stream_info = client.streams.get_stream_by_user(user_id)
        if stream_info is not None:
            if stream_info.broadcast_platform == 'live':
                status = 0  # user is streaming
            else:
                status = 3  # unexpected error
        else:
            status = 1      # user offline
    else:
        status = 2          # user not found

    return status, stream_info

def loopcheck():
    status, stream_info = check_user(user)
    if status == 2:
        print("Username not found. Invalid username?")
    elif status == 3:
        print("Unexpected error. Maybe try again later")
    elif status == 1:
        t = Timer(time, loopcheck)
        print(user,"is currently offline, checking again in",time,"seconds")
        t.start()
    elif status == 0:
        print(user,"is online. Stop.")
        filename = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" - "+user+" - "+re.sub(r"[^a-zA-Z0-9]+", ' ', stream_info['channel']['status'])+".flv"
        subprocess.call(["streamlink","https://twitch.tv/"+user,quality,"-o",filename])
        print("Stream is done. Going back to checking..")
        t = Timer(time, loopcheck)
        t.start()


def main():
    global time
    global user
    global quality

    #help
    if(len(sys.argv) == 2 and (sys.argv[1]=="help" or sys.argv[1]=="-help" or sys.argv[1]=="--help")):
        print("Usage: check.py [time] [user] [quality]")
        print("Default values: time=30 user=forsen quality=best")
        return

    if sys.argv == None or len(sys.argv) <= 1:   #No args
        time = 30.0
        user = "forsen"
        quality = "best"
    elif len(sys.argv) < 3:                     #argv[1] = time
        time = int(sys.argv[1])
        user = "forsen"
        quality = "best"
    elif len(sys.argv) < 4:                     #argv[1] = time AND argv[2] = user
        time = int(sys.argv[1])
        user = sys.argv[2]
        quality = "best"
    else:                                       #argv[1] = time AND argv[2] = user AND argv[3] = quality
        time = int(sys.argv[1])
        user = sys.argv[2]
        quality = sys.argv[3]

    if(time<15):
        print("Time shouldn't be lower than 15 seconds")
        time=15

    t = Timer(time, loopcheck)
    print("Checking for",user,"every",time,"seconds. Record with",quality,"quality.")
    loopcheck()
    t.start()


if __name__ == "__main__":
    # execute only if run as a script
    main()

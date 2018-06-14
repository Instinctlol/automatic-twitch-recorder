#This script checks if a user on twitch is currently streaming and then records the stream via streamlink
import datetime
import re
import subprocess
import sys
import os
import getopt
from threading import Timer
from twitch import TwitchClient

CLIENT_ID = 'PASTE YOUR CLIENT ID HERE AS A STRING'
# e.g. CLIENT_ID = '123456789ABCDEFG'
#

VALID_BROADCAST = [ 'live' ]
# 'rerun' can be added through commandline flags/options

def check_user(user):
    """ returns 0: online, 1: offline, 2: not found, 3: error """

    client = TwitchClient(client_id=CLIENT_ID)
    response = client.users.translate_usernames_to_ids(user)
    stream_info = 0
    if response.__len__() > 0:
        user_id = response[0].id
        stream_info = client.streams.get_stream_by_user(user_id)
        if stream_info is not None:
            if stream_info.broadcast_platform in VALID_BROADCAST:
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
        sys.exit(3)
    elif status == 3:
        print("Unexpected error. Maybe try again later")
    elif status == 1:
        t = Timer(time, loopcheck)
        print(user,"is currently offline, checking again in",time,"seconds")
        t.start()
    elif status == 0:
        print(user,"is online. Stop.")
        filename = datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S")+" - "+user+" - "+re.sub(r"[^a-zA-Z0-9]+", ' ', stream_info['channel']['status'])+".flv"
        dir = os.getcwd()+os.path.sep+user
        if not os.path.exists(dir):
            os.makedirs(dir)
        subprocess.call(["streamlink","https://twitch.tv/"+user,quality,"-o",filename], cwd=dir)
        print("Stream is done. Going back to checking..")
        t = Timer(time, loopcheck)
        t.start()

def usage():
    print("Usage: check.py [options] [user]")
    print("This script checks if a user on twitch is currently streaming and then records the stream via streamlink")
    print("    -h,--help               Display this message.")
    print("    -t,--time=TIME          Set the time interval in seconds between checks for user. Default is 30.")
    print("    -q,--quality=QUALITY    Set the quality of the stream. Default is 'best'.")
    print("    -r,--allow-rerun        Don't ignore reruns.")



def main():
    global time
    global user
    global quality

    # Defaults
    time=30.0
    quality="best"

    # Use getopts to process options and arguments.
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ht:q:r", ["help", "time=","quality=","allow-rerun"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):  # Display help message
            usage()
            sys.exit()
        elif opt in ('-t', '--time'): # Set time interval between checks for user
            try:
                time = int(arg)
            except ValueError as ex:
                print('"%s" cannot be converted to an int: %s' % (arg, ex))
                print("Using default: %ds" %(time))
                print("")
        elif opt in ("-q", "--quality"): # Set quality
            quality = arg
        elif opt in ("-r", "--allow-rerun"): # Allow recording of reruns
            VALID_BROADCAST.append('rerun')

    # Checking if the remaining arguments are valid.
    if len(args) > 1:
        user = " ".join(args)
        print("'%s' is not a valid username" %(user))
        print("")
        usage()
        sys.exit(2)

    # Check if user is supplied.
    user = "".join(args)
    if user == "":
        print("User not supplied")
        usage()
        sys.exit(2)

    if(time<15):
        print("Time shouldn't be lower than 15 seconds")
        time=15


    if CLIENT_ID == 'PASTE YOUR CLIENT ID HERE AS A STRING':
        print("You must edit the CLIENT_ID variable in this script with your personal client id.")
        print("https://blog.twitch.tv/client-id-required-for-kraken-api-calls-afbb8e95f843")
        sys.exit(4)

    t = Timer(time, loopcheck)
    print("Checking for",user,"every",time,"seconds. Record with",quality,"quality.")
    loopcheck()
    t.start()


if __name__ == "__main__":
    # execute only if run as a script
    main()

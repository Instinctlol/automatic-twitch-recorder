#This script checks if a user on twitch is currently streaming and then records the stream via livestreamer

from urllib.request import urlopen
from urllib.error import URLError
from threading import Timer
import json
import sys
import subprocess
import datetime


def check_user(user):
    """ returns 0: online, 1: offline, 2: not found, 3: error """
    global info
    url = 'https://api.twitch.tv/kraken/streams/' + user
    try:
        info = json.loads(urlopen(url, timeout = 15).read().decode('utf-8'))
        if info['stream'] == None:
            status = 1
        else:
            status = 0
    except URLError as e:
        if e.reason == 'Not Found' or e.reason == 'Unprocessable Entity':
            status = 2
        else:
            status = 3
    return status

def format_filename(fname):
    fname = fname.replace("/","")
    fname = fname.replace("?","")
    fname = fname.replace(":","-")
    fname = fname.replace("\\","")
    fname = fname.replace("<","")
    fname = fname.replace(">","")
    fname = fname.replace("*","")
    fname = fname.replace("\"","")
    fname = fname.replace("|","")
    return fname


def loopcheck():
    status = check_user(user)
    if status == 2:
        print("username not found. invalid username?")
    elif status == 3:
        print("unexpected error. maybe try again later")
    elif status == 1:
        t = Timer(time, loopcheck)
        print(user,"currently offline, checking again in",time,"seconds")
        t.start()
    elif status == 0:
        print(user,"online. stop.")
        filename = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" - "+user+" - "+(info['stream']).get("channel").get("status")+".flv"
        filename = format_filename(filename)
        subprocess.call(["livestreamer","twitch.tv/"+user,quality,"-o",filename])
        print("Stream is done. Going back to checking..")
        t = Timer(time, loopcheck)
        t.start()


def main():
    global time
    global user
    global quality
    
    #help
    if(sys.argv != None and (sys.argv[1]=="help" or sys.argv[1]=="-help" or sys.argv[1]=="--help")):
        print("Usage: check.py [time] [user] [quality]")
        print("Default values: time=30 user=sing_sing quality=best")
        return
    
    if sys.argv == None or len(sys.argv) < 2:   #No args
        time = 30.0
        user = "sing_sing"
        quality = "best"
    elif len(sys.argv) < 3:                     #argv[1] = time
        time = int(sys.argv[1])
        user = "sing_sing"
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
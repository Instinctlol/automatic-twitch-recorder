#This script checks if a user on twitch is currently streaming and then records the stream via streamlink
import datetime
import re
import subprocess
import sys
import os
import shutil
import getopt
import TwitchRecord as tr
from threading import Timer


def usage():
    print("Usage: check.py [options] [user]")
    print("This script checks if a user on twitch is currently streaming and then records the stream via streamlink")
    print("    -h,--help               Display this message.")
    print("    -t,--time=TIME          Set the time interval in seconds between checks for user. Default is 30.")
    print("    -q,--quality=QUALITY    Set the quality of the stream. Default is 'best'. See streamlink documentation for more details.")
    print("    -c,--client-id=ID       Override the client id. The script will ask for an id if not given or stored in a configuration file.")
    print("    -r,--allow-rerun        Don't ignore reruns.")
    print("    -d,--rec-dir=DIRECTORY  Set the recording directory.")
    print("    -o,--out-dir=DIRECTORY  Set the final directory.")
    print("    -f,--ffmpeg             Convert the file with ffmpeg after finished recording.")
    print("    -k,--keep               Keep the source file after converting.")

def loopcheck(stream):
    if not stream.valid_user():
        print("Username not found. Invalid username?")
        sys.exit(3)
    elif stream.is_online():
        print(stream.user,"is online. Stop.")
        stream.filename = datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S")+" - "+stream.user+" - "+re.sub(r"[^a-zA-Z0-9]+", ' ', stream.stream_info['channel']['status'])+".flv"
        if not os.path.exists(stream.recdir):
            os.makedirs(stream.recdir)
        subprocess.call(["streamlink","https://twitch.tv/"+stream.user,stream.quality,"-o",stream.filename], cwd=stream.recdir)
        if stream.conv:
            subprocess.call(['ffmpeg','-y', '-i',stream.filename, '-c:v', 'libx265', '-crf', '28', '-c:a', 'aac', '-strict', '-2', stream.filename+'.x265.mkv'], cwd=stream.recdir)
            if not stream.keep:
                os.remove(stream.recdir+os.path.sep+stream.filename)
            stream.filename = stream.filename+".x265.mkv"
        if stream.outdir is not None:
            print("Moving file to "+stream.outdir)
            if not os.path.exists(stream.outdir):
                os.makedirs(stream.outdir)
            shutil.move(stream.recdir+os.path.sep+stream.filename,stream.outdir+os.path.sep+stream.filename)
        print("Stream is done. Going back to checking..")
        t = Timer(stream.time, loopcheck, args=[stream])
        t.start()
    else:
        t = Timer(stream.time, loopcheck, args=[stream])
        print(stream.user,"is currently offline, checking again in",stream.time,"seconds")
        t.start()


def main():
    # Defaults
    time=30.0
    quality="best"
    rerun=False
    outdir=None
    recdir=None
    conv=False
    keep=False



    # Use getopts to process options and arguments.
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ht:q:c:rd:o:fk", ["help", "time=","quality=","client-id=","allow-rerun","rec-dir=","out-dir=","ffmpeg","keep"])
    except getopt.GetoptError as ex:
        print(ex)
        usage()
        sys.exit(2)

    # Check if user is supplied.
    user = "".join(args)
    if user == "":
        print("User not supplied")
        usage()
        sys.exit(2)

    # Checking if the remaining arguments are valid.
    if len(args) > 1:
        user = " ".join(args)
        print("'%s' is not a valid username" %(user))
        print("")
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
            if(time<15):
                print("Time shouldn't be lower than 15 seconds")
                time=15
        elif opt in ("-q", "--quality"): # Set quality
            quality = arg
        elif opt in ("-r", "--allow-rerun"): # Allow recording of reruns
            rerun = True
        elif opt in ("-c", "--client-id"): # Override client id
            tr.CLIENT_ID = arg
        elif opt in ("-d", "--rec-dir"): # Set recording directory
            recdir = arg
        elif opt in ("-o", "--out-dir"): # Set output directory
            outdir = arg
        elif opt in ("-f", "--ffmpeg"): # Set output directory
            conv = True
        elif opt in ("-k", "--keep"): # Set output directory
            keep = True


    if tr.CLIENT_ID == '':
        tr.check_client_id()


    stream = tr.TwitchUser(user, time=time, quality=quality, rerun=rerun)
    if recdir is not None:
        stream.recdir = recdir
    if outdir is not None:
        stream.outdir = outdir
    if conv:
        stream.conv=True
    if keep:
        stream.keep=True


    print("Checking for",stream.user,"every",stream.time,"seconds. Record with",stream.quality,"quality.")
    loopcheck(stream)


if __name__ == "__main__":
    # execute only if run as a script
    main()

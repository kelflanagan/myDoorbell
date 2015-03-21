########################################################################
# Author: J. Kelly Flanagan
# Copyright (c) 2015
#
# get_ringtone.py connects to a ringtone server and downloads a ringtone
# when needed.
#
# This program is intended to be started each minute by cron and either
# exits due to success or failure. Success when nothing happens or a new
# ringtone or two are downloaded.
#
# get_ringtone.py attempts to do the following:
#
# 1. open the file $HOME/myDoorbell/myDoorbellInit and read its content
#    into a dicitonary. This file contains cofiguration server name, keys
#    and other necessary credentials. If this file doesn't exist we exit
#    with an error.
# 2. open the file $HOME/myDoorbell/myDoorbellConfig and read its content
#    into a dictionary. If the file does not exist we exit with an error
# 3. use configuration dictionary to determine if a new ringtone is needed.
#    If a new ringtone is needed and there is not a file named 
#    myDoorbellAcquired[Front | Rear].tmp then create the temporary file 
#    and get the ringtone. If the temporary file exists exit without error.
#    If a ringtone is not needed remove the temporary file and exit 
#    without error.
########################################################################

#!/usr/local/bin/python

import requests
import os
import ast
import json
import time

myDoorbellInit = {}
myDBConfig = {}

def get_init(home):
    global myDoorbellInit
    try:
        kf = open(home + '/myDoorbell/myDoorbellInit', 'r')
    except IOError:
        return False
    else:
        key_file = kf.read()
        myDoorbellInit = ast.literal_eval(key_file)
        kf.close()
        return True

# let the ringtone server know that we acquired the ringtone so it
# can reset the flag. If it fails it returns False otherwise True
def got_ringtone(bell):
    # form headers for json
    headers = {'content-type': 'application/json'}
    # only supported method
    method = 'POST'
    # resource
    resource = ("/sky/event/" + myDoorbellInit['eci'] + '/12345')
    # JSON payload
    payload = ({'_domain':'myDoorbell', '_type':'got' + 
                bell.capitalize() + 'Ringtone', '_async':'true'})
    # server +
    url = 'https://' + myDoorbellInit['config_server'] + resource 

    # make request
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    if response.status_code == requests.codes.ok:
        return True
    else:
        return False

# Acquire requested ringtone, write it to a temporary file, and rename it
# to make the transaction atomic
def get_ringtone(bell, home):
    # form url
    url = ('https://' + myDoorbellInit['config_server'] + 
           '/sky/cloud/' + myDoorbellInit['rid'] + 
           '/myDoorbellRingtone?door=' + bell +
           '&_eci=' + myDoorbellInit['eci'])

    # make request
    try:
        r = requests.get(url)
    except r.ConnectionError:
        print "Connection error -", (time.strftime("%H:%M:%S"))
        return False
    except:
        print "Other error -", (time.strftime("%H:%M:%S"))
        return False
    else:
        if r.status_code == requests.codes.ok:
            # acquire dictionary
            new_dict = r.json()
            # extract JSON value as unicode string
            ustr = new_dict['ringtone_file']
            # encode string with latin1, this permits writing raw files
            hex_str = ustr.encode('latin1')

            # write file to $HOME/myDoorbell/myDoorbellRingtone[bell].tmp
            # for filename
            fn = home + '/myDoorbell/myDoorbellRingtone' + bell.capitalize()
            tmp = fn + '.tmp'
            try:
                f = open(tmp,'wb')
            except IOError:
                print "Error opening tmp ringtone file for writing"
                return False
            else:
                f.write(hex_str)
                f.close()
                # move file atomically 
                os.rename(tmp, fn)
                print "Update -", (time.strftime("%H:%M:%S"))
                return True
        else:
            print "Bad response -", (time.strftime("%H:%M:%S"))
            return False
    return False

# Start of program
# get home directory
home_dir = '/home'

# get eci and rid
if get_init(home_dir) == False:
    print "Can't open initialization file %s" % (home_dir + '/myDoorbell/myDoorbellInit')
    exit(-1)

# read configuration file as it is needed multiple times in this service
try:
    cf = open(home_dir + '/myDoorbell/myDoorbellConfig', 'r')
except IOError:
    print 'Cant open configuration file'
    exit(-1)
else:
    myDBConfig = ast.literal_eval(cf.read())
    cf.close()

# Determine if a new ringtone is needed. if it is and there is no Acquired file
# get the ringtone, create the Acquired file, and let the server know by raising
# an event. Otherwise we quietly exit and try again later.
#
# form $HOME/myDoorbell/myDoorbellAcquired[Front | Rear].tmp file names
AcquiredFront = home_dir + '/myDoorbell/myDoorbellAcquireFront.tmp'
AcquiredRear = home_dir + '/myDoorbell/myDoorbellAcquireRear.tmp'

if myDBConfig['ringtone_new_front'] == 'true':
    print 'Config file indicates front ringtone is needed'
    if os.path.isfile(AcquiredFront) == False:
        print 'Acquired file does not exist, get ringtone'
        if get_ringtone('front', home_dir) == True:
            # create Acquired file
            with open(AcquiredFront, 'a'):
                os.utime(AcquiredFront, None)
            if got_ringtone('front') == False:
                print 'Failure to ack front ringtone'
            else:
                print 'Got event sent successfully'
        else:
            print 'Failed to get front ringtone'
    else:
        print 'Front Acquired file exists'
else:
    print 'Config file indicates front ringtone is not needed'
    if os.path.isfile(AcquiredFront) == True:
        print 'Acquired file exists, romove it'
        os.remove(AcquiredFront)

if myDBConfig['ringtone_new_rear'] == 'true':
    print 'Config file indicates rear ringtone is needed'
    if os.path.isfile(AcquiredRear) == False:
        print 'Acquired file does not exist, get ringtone'
        if get_ringtone('rear', home_dir) == True:
            # create Acquired file
            with open(AcquiredRear, 'a'):
                os.utime(AcquiredRear, None)
            if got_ringtone('rear') == False:
                print 'Failure to ack rear ringtone'
            else:
                print 'Got event sent successfully'
        else:
            print 'Failed to get rear ringtone'
    else:
        print 'Rear Acquired file exists'
else:
    print 'Config file indicates rear ringtone is not needed'
    if os.path.isfile(AcquiredRear) == True:
        print 'Acquired file exists, romove it'
        os.remove(AcquiredRear)


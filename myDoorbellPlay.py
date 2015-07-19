########################################################################
# Author: J. Kelly Flanagan
# Copyright (c) 2015
#
# myDoorbellPlay.py plays the doorbell ringtone and raises an event when 
# the doorbell is asserted. 
#
# myDoorbellPlay.py attempts to do the following:
#
# 1. waits for the front or rear doorbell to be asserted
# 2. when a button is asserted the configuration file is read to a
#    global variable myDoorbellConfig for later use
# 3. start a process to raise event
# 4. start a process to play ringtone
# 5. wait for both processes to complete
########################################################################

#!/usr/local/bin/python

import subprocess
import ast
import json
import threading
import requests
import time

#myDoorbellHomeDir = '/home'
myDoorbellHomeDir = '/users/kelly/dropbox/src'
myDoorbellConfig = {}

# read configuration file
# read in the configuration file if it exists and store in a dictionary
def get_config():
    global myDoorbellConfig

    try:
        f = open(myDoorbellHomeDir + '/myDoorbell/myDoorbellConfig', 'r')
    except IOError: 
        print "Can't open config file %s" % (myDoorbellHomeDir + '/myDoorbell/myDoorbellConfig')
        return False
    else:
        my_string = f.read()
        myDoorbellConfig = ast.literal_eval(my_string)
        f.close()
    return True
# end function

# set volume
def set_volume(bell):
    global myDoorbellConfig

    mixer_str = "/usr/local/bin/amixer -q -c 0 set PCM "
    if bell == 'front':
        if myDoorbellConfig['silent_front'] == 'true':
            mixer_str = mixer_str + "0%"
        else:
            mixer_str = mixer_str + str(myDoorbellConfig['volume_front']) + "%"
    elif bell == 'rear':
        if myDoorbellConfig['silent_rear'] == 'true':
            mixer_str = mixer_str + "0%"
        else:
            mixer_str = mixer_str + str(myDoorbellConfig['volume_rear']) + "%"
    else:
        return False
    
    print mixer_str
#JKF    subprocess.call(mixer_str, shell=True)
    
    return True
# end function

# raise event
# from the config file get the method, resource, and payload to
# raise the event, then raise it
def raise_event(bell):
    # get method
    method = myDoorbellConfig['webhook_method']

    # form headers
    if method.upper() == 'POST' or method.upper() == 'PUT':
        headers = {'content-type': 'application/json'}
    elif method.upper() == 'GET':
        headers = {'content-type': 'application/x-www-form-urlencoded'}
    else:
        return False

    # get and form resource - webhook_resource_rear | front
    resource_key = 'webhook_resource_' + bell
    resource = myDoorbellConfig[resource_key]

    # get payload key and payload
    payload_key = 'webhook_payload_' + bell
    payload = myDoorbellConfig[payload_key]

    # server +
    if method.upper() == 'POST' or method.upper() == 'PUT':
        url = 'https://' + myDoorbellConfig['webhook_server'] + resource + '/12345'
    elif method.upper() == 'GET':
        url = ('https://' + myDoorbellConfig['webhook_server'] + resource + '/12345' +
               '?' + payload)
    else:
        return False

    # make request
    try:
        if method.upper() == 'POST':
            response = requests.post(url, data=payload, headers=headers)
        elif method.upper() == 'PUT':
            response = requests.put(url, data=payload, headers=headers)
        elif method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        else:
            return False
    except requests.ConnectionError:
        print "Connection error"
        return False
    except:
        print "Other error"
        return False
    else:
        if response.status_code == requests.codes.ok:
            return True
        else:
            return False
# end function

# begin here
# wait for asserted front or rear bell
# this code get written later
# top:
# front or rear bell was rung
raw_input("Press Enter to ring front bell")

bell = 'front'

# get current configuration file
if get_config() == False:
    print 'get config failed'

t = threading.Thread(target=raise_event, args=(bell))
t.daemon=True
t.start()

print 'rang bell'
time.sleep(10)

#if play_ringtone(bell) == False:
#    print 'play ringtone failed'

# wait until both threads return
# back to top

########################################################################
# Author: J. Kelly Flanagan
# Copyright (c) 2015
#
# get_config.py connects to a configuration server and downloads the 
# device configuration data and store it to a file.
########################################################################

#!/usr/local/bin/python

import requests
import os
import ast
import json
import time

myDoorbellKeys = {}
myDBConfig = {}

def get_keys():
    global myDoorbellKeys
    try:
        kf = open('myDoorbellKeys', 'r')
    except IOError:
        return False
    else:
        key_file = kf.read()
        myDoorbellKeys = ast.literal_eval(key_file)
        kf.close()
        return True

# function make_https_request
# parameters: server - fully qualified doamin name
#             resource - url
#             parameters - include the ?
# returns: response object as defined by requests
def make_https_request(server, resource, parameters):
    url = "https://" + server + resource + parameters
    response = requests.get(url)
    return response

# let the ringtone server know that we acquired the ringtone so it
# can reset the flag. If it fails it returns False otherwise True
def got_ringtone(bell):
    # form headers for json
    headers = {'content-type': 'application/json'}
    # only supported method
    method = 'POST'
    # resource
    resource = ("/sky/event/" + myDoorbellKeys['eci'] + '/12345')
    # JSON payload
    payload = ({'_domain':'myDoorbell', '_type':'got' + 
                bell.capitalize() + 'Ringtone', '_async':'true'})
    # server +
    url = 'https://cs.kobj.net' + resource 

    # make request
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    if response.status_code == requests.codes.ok:
        return True
    else:
        return False


# Acquire requested ringtone, write it to a temporary file, and rename it
# to make the transaction atomic
def get_ringtone(bell):
    # form resource and parameters
    resource = "/sky/cloud/" + myDoorbellKeys['rid'] + "/myDoorbellRingtone"
    parameters = "?door=" + bell + "&_eci=" + myDoorbellKeys['eci']

    # make request
    try:
        r = make_https_request("cs.kobj.net", resource, parameters)
    except r.ConnectionError:
        print "Connection error -", (time.strftime("%H:%M:%S"))
        return False
    except:
        print "Other error -", (time.strftime("%H:%M:%S"))
        return False
    else:
        if r.status_code == 200:
            # acquire dictionary
            new_dict = r.json()
            # extract JSON value as unicode string
            ustr = new_dict['ringtone_file']
            # encode string with latin1, this permits writing raw files
            hex_str = ustr.encode('latin1')

            # write file to /tmp/myDoorbellRingtone[bell].tmp
            # for filename
            fn = '/tmp/myDoorbellRingtone' + bell.capitalize()
            tmp = fn + '.tmp'
            try:
                f = open(tmp,'wb')
            except IOError:
                print "Error opening ringtone file for writing"
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
# get eci and rid
if get_keys() == False:
    print "Can't open key file, exiting"
    exit(-1)

# read configuration file as it is needed multiple times in this service
try:
    cf = open('/tmp/myDoorbellConfig', 'r')
except IOError:
    print 'Cant open configuration file'
    exit(-1)
else:
    myDBConfig = ast.literal_eval(cf.read())
    cf.close()

# Determine if a new ringtone is needed. if it is, get it.  Let the server
# know we got it
if myDBConfig['ringtone_new_front'] == 'true':
    if get_ringtone('front') == False:
        print 'Failed to get front ringtone'
    else:
        if got_ringtone('front') == False:
            print 'Failure to ack front ringtone'

if myDBConfig['ringtone_new_rear'] == 'true':
    if get_ringtone('rear') == False:
        print 'Failed to get rear ringtone'
        if got_ringtone('rear') == False:
            print 'Failure to ack rear ringtone'


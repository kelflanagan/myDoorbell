########################################################################
# Author: J. Kelly Flanagan
# Copyright (c) 2015
#
# get_ringtone.py connects to a ringtone server and downloads a
# ringtone and stores it to a file for the front or rear bell.
########################################################################

#!/usr/bin/python

import requests
import os
import ast
import time
import json

# function make_https_request
# parameters: server - fully qualified doamin name
#             resource - url
#             parameters - include the ?
# returns: response object as defined by requests
def make_https_request(server, resource, parameters):
    url = "https://" + server + resource + parameters
    response = requests.get(url)
    return response

# function make_https_post
# parameters: server - fully qualified doamin name
#             resource - url
#             parameters - include the ?
#             data - payload
# returns: response object as defined by requests
def make_https_post(server, resource, parameters, payload, header):
    url = 'https://' + server + resource + parameters
    response = requests.post(url, data=ast.literal_eval(payload), headers=header)
    return response

# let the ringtone server know that we acquired the ringtone so it
# can reset the flag
def got_ringtone(bell):
    # get ack method
    method = myDBConfig['ringtone_ack_method']
    # get ringtone_ack resource
    resource = myDBConfig['ringtone_ack_resource_' + bell]
    # form ack payload
    payload = myDBConfig['ringtone_ack_payload_' + bell]
    # form headers
    headers = {'content-type': 'application/json'}

    # only support POST currently
    if method == 'POST':
        make_https_post('cs.kobj.net', resource, '', payload, headers)
    else:
        print 'Only POST supported'

# Acquire requested ringtone, write it to a temporary file, and rename it
# to make the transaction atomic
def get_ringtone(bell):
    # acquire and form resource. This resource includes  parameters
    resource = myDBConfig['ringtone_resource_' + bell]
    # make request
    try:
        r = make_https_request("cs.kobj.net", resource, '')
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

# read configuration file as it is needed multiple times in this service
try:
    cf = open('/tmp/myDoorbellConfig', 'r')
except IOError:
    print 'Cant open configuration file'
    exit(0)
else:
    myDBConfig = ast.literal_eval(cf.read())
    cf.close()

# Determine if a new ringtone is needed. if it is, get it.  Let the server
# know we got it
if myDBConfig['ringtone_new_front'] == 'true':
    print 'Should get front ringtone'
    if get_ringtone('front'):
        got_ringtone('front')

if myDBConfig['ringtone_new_rear'] == 'true':
    print 'Should get rear ringtone'
    if get_ringtone('rear'):
        got_ringtone('rear')

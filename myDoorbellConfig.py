########################################################################
# Author: J. Kelly Flanagan
# Copyright (c) 2015
#
# myDoorbellConfig.py connects to a configuration server and downloads the 
# device configuration data, acts on it, and stores it to a file.
#
# This program is intended to be started each minute by cron and either
# exits due to success or failure.
#
# myDoorbellConfig.py attempts to do the following:
#
# 1. open the file myDoorbellHomeDir/myDoorbell/myDoorbellInit and read its 
#    content into a dicitonary. This file contains cofiguration server name, 
#    keys and other necessary credentials. If this file doesn't exist we exit
#    with an error.
# 2. open the file myDoorbellHomeDir/myDoorbell/myDoorbellConfig and read its 
#    content into a dictionary. If the file does not exist a empty dictionary
#    is used.
# 3. use configuration server name, rid, eci, and other items to form 
#    a url for requesting the configuration information from the
#    configuration server. If an exception occurs simply exit and we'll
#    try again later.
# 4. if success, otherwise exit and we'll try again later.
# 5. get returned JSON config into dictionary. If ringtones are required
#    download them. If ringtones are acquired acknowledge the download. 
#    Compare config to previous version with the exception of the ringtone
#    elements. If they differ store the results into a temporary file
#    and then use rename to make an atomic update. If they do not differ
#    simply exit.
########################################################################

#!/usr/local/bin/python

import requests
import os
import ast
import json
import time
import signal

# keys = home_dir, config_server, eci, rid
myDoorbellInit = {}
myDoorbellHomeDir = '/Users/kelly'

# fill myDoorbellInit global dictionary
def get_init():
    global myDoorbellInit
    global myDoorbellHomeDir
    try:
        kf = open(myDoorbellHomeDir + '/myDoorbell/myDoorbellInit', 'r')
    except IOError:
        return False
    else:
        key_file = kf.read()
        myDoorbellInit = ast.literal_eval(key_file)
        kf.close()
        return True
# end function

# let the ringtone server know that we acquired the ringtone so it
# can reset the flag in the cloud based config file. If it fails return False
def got_ringtone(bell):
    # form headers for json
    headers = {'content-type': 'application/json'}
    # resource
    resource = ("/sky/event/" + myDoorbellInit['eci'] + '/12345')
    # JSON payload
    payload = ({'_domain':'myDoorbell', '_type':'got' + 
                bell.capitalize() + 'Ringtone', '_async':'true'})
    # server +
    url = 'https://' + myDoorbellInit['config_server'] + resource 

    # make request
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
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

# Acquire requested ringtone, write it to a temporary file, and rename it
# to make the transaction atomic, on success return True, on failure False
def get_ringtone(bell):
    global myDoorbellHomeDir
    # form url
    url = ('https://' + myDoorbellInit['config_server'] + 
           '/sky/cloud/' + myDoorbellInit['rid'] + 
           '/myDoorbellRingtone?door=' + bell +
           '&_eci=' + myDoorbellInit['eci'])

    # make request
    try:
        r = requests.get(url)
    except requests.ConnectionError:
        print "Connection error"
        return False
    except:
        print "Other error"
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
            fn = (myDoorbellHomeDir + 
                  '/myDoorbell/myDoorbellRingtone' + bell.capitalize())
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
                print "Update %s ringtone" % bell
                return True
        else:
            print "Bad response"
            return False
    return False

# get_rintones checks for the need, acquires the ringtone, 
# acknowledges it, and returns
def get_ringtones(dict):
    ret_val = False
    if dict['ringtone_new_front'] == 'true':
        ret_val = True
        print 'Config file indicates front ringtone is needed'
        # reset flag indicating need. If acquisition fails we'll catch
        # it on the next iteration
        if get_ringtone('front') == True:
            if got_ringtone('front') == True:
                print 'Got event sent successfully'
            else:
                print 'Failure to ack front ringtone'
        else:
            print 'Failed to get front ringtone'

    if dict['ringtone_new_rear'] == 'true':
        ret_val = True
        print 'Config file indicates rear ringtone is needed'
        # reset flag indicating need. If acquisition fails we'll catch
        # it on the next iteration
        if get_ringtone('rear') == True:
            if got_ringtone('rear') == True:
                print 'Got event sent successfully'
            else:
                print 'Failure to ack rear ringtone'
        else:
            print 'Failed to get rear ringtone'
    return ret_val
# end of fucntion

# check to see if this program is already running. If it is then return
# True unless it has been doing so for more than 10 minutes. In that case
# kill it and return False.
def myDoorbell_is_running():
    pf = '/tmp/myDoorbell.pid'
    pid = str(os.getpid())

    if os.path.isfile(pf):
        # if pid file hasn't been updated for some time then delete it,
        # run, and create a new one
        age = time.time() - os.path.getmtime(pf)
        if age > 600:  # 10 minutes
            # get previous pid
            opid = open(pf).read()
            # delete PID file
            try:
                os.kill(int(opid), signal.SIGKILL)
            except:
                print "exception on kill"
            # write file
            file(pf, 'w').write(pid)
            return False
        else:
            print "%s already exists" % pf
            return True
    else:
        file(pf, 'w').write(pid)
        return False
# end of function

# Program execution begins here
# check to see if we're running
if myDoorbell_is_running():
    exit(0)

# get eci, rid, server name, and home. into global dictionary
# named myDoorbellInit
if get_init() == False:
    print "Can't open initialization file %s" % (home_dir + '/myDoorbell/myDoorbellInit')
    print 'removing pid file'
    os.remove('/tmp/myDoorbell.pid')
    exit(-1)

# read in the configuration file if it exists and store in a dictionary
# if it doesn't exist then create an empty dictionary
try:
    f = open(myDoorbellHomeDir + '/myDoorbell/myDoorbellConfig', 'r')
except IOError:
    old_dict = {}
else:
    my_string = f.read()
    old_dict = ast.literal_eval(my_string)
    f.close()

# get the configuration from the config server
# form url
url = ('https://' + myDoorbellInit['config_server'] + 
       '/sky/cloud/' + myDoorbellInit['rid'] + 
       '/myDoorbellConfig?_eci=' + myDoorbellInit['eci'])
try:
    response = requests.get(url)
except requests.ConnectionError:
    print "Connection error"
except:
    print "Other error"
else:
    if response.status_code == requests.codes.ok:
        # acquire dictionary
        new_dict = response.json()

        # act on configuration data
        if get_ringtones(new_dict):
            new_dict['ringtone_new_front'] = 'false'
            new_dict['ringtone_new_rear'] = 'false'
            
        if cmp(new_dict, old_dict) != 0:
            # write config file to $HOME/myDoorbell/myDoorbellConfig.tmp
            try:
                f = open(myDoorbellHomeDir + '/myDoorbell/myDoorbellConfig.tmp','w')
            except IOError:
                print "Error opening config file for writing"
            else:
                f.write(str(new_dict))
                f.close()
            os.rename(myDoorbellHomeDir + '/myDoorbell/myDoorbellConfig.tmp', 
                      myDoorbellHomeDir + '/myDoorbell/myDoorbellConfig')
            old_dict = new_dict
            print "Update"
        else:
            print "Success"
    else:
        print "Bad response"

#clean up before we leave
print 'removing pid file'
os.remove('/tmp/myDoorbell.pid')

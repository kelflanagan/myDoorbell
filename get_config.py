########################################################################
# Author: J. Kelly Flanagan
# Copyright (c) 2015
#
# get_ringtone.py connects to a configuration server and downloads the 
# device configuration data and store it to a file.
#
# This program is intended to be started each minute by cron and either
# exits due to success or failure.
#
# get_config.py attempts to do the following:
#
# 1. open the file $HOME/myDoorbell/myDoorbellInit and read its content
#    into a dicitonary. This file contains cofiguration server name, keys
#    and other necessary credentials. If this file doesn't exist we exit
#    with an error.
# 2. open the file $HOME/myDoorbell/myDoorbellConfig and read its content
#    into a dictionary. If the file does not exist a empty dictionary
#    is used.
# 3. use configuration server name, rid, eci, and other items to form 
#    a url for requesting the configuration information from the
#    configuration server. If an exception occurs simply exit and we'll
#    try again later.
# 4. if success and a 20+ HTTP response is received proceed, otherwise
#    exit and we'll try again later.
# 5. get returned JSON config into dictionary. Compare to previous
#    version. If they differ store the results into a temporary file
#    and then use rename to make an atopic update. If they do not differ
#    simply exit.
########################################################################

#!/usr/local/bin/python

import requests
import os
import ast
import time

myDoorbellInit = {}

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
    
# Program execution begins here
# find home
home_dir = '/home'

# get eci, rid, server name, etc. into global dictionary
# named myDoorbellInit
if get_init(home_dir) == False:
    print "Can't open initialization file %s" % (home_dir + '/myDoorbell/myDoorbellInit')
    exit(-1)

# read in the configuration file if it exists and store in a dictionary
# if it doesn't exist then create an empty dictionary
try:
    f = open(home_dir + '/myDoorbell/myDoorbellConfig', 'r')
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
    print "Connection error -", (time.strftime("%H:%M:%S"))
except:
    print "Other error -", (time.strftime("%H:%M:%S"))
else:
    if response.status_code == requests.codes.ok:
        # acquire dictionary
        new_dict = response.json()
        if cmp(new_dict, old_dict) != 0:
            # write config file to $HOME/myDoorbell/myDoorbellConfig.tmp
            try:
                f = open(home_dir + '/myDoorbell/myDoorbellConfig.tmp','w')
            except IOError:
                print "Error opening config file for writing"
            else:
                f.write(str(new_dict))
                f.close()
            os.rename(home_dir + '/myDoorbell/myDoorbellConfig.tmp', 
                      home_dir + '/myDoorbell/myDoorbellConfig')
            old_dict = new_dict
            print "Update -", (time.strftime("%H:%M:%S"))
        else:
            print "Success -", (time.strftime("%H:%M:%S"))
    else:
        print "Bad response -", (time.strftime("%H:%M:%S"))

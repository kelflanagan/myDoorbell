########################################################################
# Author: J. Kelly Flanagan
# Copyright (c) 2015
#
# get_ringtone.py connects to a configuration server and downloads the 
# device configuration data and store it to a file.
########################################################################

#!/usr/local/bin/python

import requests
import os
import ast
import time

myDoorbellKeys = {}

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
    
def make_https_request(server, resource, parameters):
    url = "https://" + server + resource + "?" + parameters
    response = requests.get(url)
    return response

# Start of program
# get eci and rid
if get_keys() == False:
    print "Can't open key file, exiting"
    exit(-1)

# read in the configuration file if it exists and store in a dictionary
# if it doesn't exist then create an empty dictionary
try:
    f = open('/tmp/myDoorbellConfig', 'r')
except IOError:
    old_dict = {}
else:
    my_string = f.read()
    old_dict = ast.literal_eval(my_string)
    f.close()

# get the configuration from the config server
try:
    response = make_https_request("cs.kobj.net",
                                  "/sky/cloud/" + myDoorbellKeys['rid'] + "/myDoorbellConfig",
                                  "_eci=" + myDoorbellKeys['eci'])
except requests.ConnectionError:
    print "Connection error -", (time.strftime("%H:%M:%S"))
except:
    print "Other error -", (time.strftime("%H:%M:%S"))
else:
    if response.status_code == 200:
        # acquire dictionary
        new_dict = response.json()
        if cmp(new_dict, old_dict) != 0:
            # write configuration to file located at /tmp/myDoorbellConfig.tmp
            try:
                f = open('/tmp/myDoorbellConfig.tmp','w')
            except IOError:
                print "Error opening config file for writing"
            else:
                f.write(str(new_dict))
                f.close()
            os.rename('/tmp/myDoorbellConfig.tmp', '/tmp/myDoorbellConfig')
            old_dict = new_dict
            print "Update -", (time.strftime("%H:%M:%S"))
        else:
            print "Success -", (time.strftime("%H:%M:%S"))
    else:
        print "Bad response -", (time.strftime("%H:%M:%S"))

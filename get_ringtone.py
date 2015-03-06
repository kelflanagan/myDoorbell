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
import time
import codecs

def make_https_request(server, resource, parameters):
    url = "https://" + server + resource + "?" + parameters
    response = requests.get(url)
    return response

# get the configuration from the config server
try:
    response = make_https_request("cs.kobj.net",
                                  "/sky/cloud/b502118x0.dev/myDoorbellRingtone",
                                  "door=front&_eci=C695CE4E-0B91-11E3-9DB3-90EBE71C24E1")
except requests.ConnectionError:
    print "Connection error -", (time.strftime("%H:%M:%S"))
except:
    print "Other error -", (time.strftime("%H:%M:%S"))
else:
    if response.status_code == 200:
        # acquire dictionary
        new_dict = response.json()
        print new_dict['ringtone_file']
        # write configuration to file located at /tmp/myDoorbellConfig.tmp
#        try:
#            f = open('/tmp/myDoorbellRingtone.tmp','wb')
#        except IOError:
#            print "Error opening ringtone file for writing"
#        else:
#            ustr = new_dict['ringtone_file']
#            bytes = ustr.encode('ascii', 'ignore')
#            f.write(bytes)
#            f.close()
#            os.rename('/tmp/myDoorbellConfig.tmp', '/tmp/myDoorbellConfig')
#            old_dict = new_dict
#            print "Update -", (time.strftime("%H:%M:%S"))
    else:
        print "Bad response -", (time.strftime("%H:%M:%S"))

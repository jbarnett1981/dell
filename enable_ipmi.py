#!/usr/bin/python

'''
Created `11/25/2014 04:30`

@author jbarnett@tableausoftware.com
@version 0.1

enable_ipmi.py: enable IPMI on a list of hosts dumped by zquery.py.
'''

import rac
import subprocess
import urllib2

drac_user = "root"
drac_pass = "PASSWORD"

def enable_ipmi(dracname):
    try:
        rac_admin = rac.RAC(dracname, drac_user, drac_pass)
        print("{0}: {1}".format(dracname, rac_admin.run_command("config -g cfgIpmiLan -o cfgIpmiLanEnable 1")))
    except urllib2.URLError as e:
        print("Error:", e)

f = open('build_servers2.txt', 'r')
for line in f:
    host = line.split()[0]
    dracname = host + "-drac.tsi.lan"
    enable_ipmi(dracname)
f.close()

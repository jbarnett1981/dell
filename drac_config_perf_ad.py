#!/usr/bin/python

'''
Created `03/27/2015 03:02`

@author jbarnett@tableausoftware.com
@version 0.1

dell_config_perf_ad.py: from servers.txt configure Active Directory authentication (standard schema) using racadm
Uses standard threading library to run jobs in parallel.

TO DO:
- fix formatting to console (line break issues)
- add logging
'''

import socket
import subprocess
import urllib2
import threading
import os

drac_user = "root"
drac_pass = "PASSWORD"
domain = "tsi.lan"

def getIP(hostname):
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return 0

def mainConfig(dracname):

    try:
        getIP(dracname)
    except:
        print("DRAC not in DNS")
        pass
    try:
        print("Configuring %s" % dracname)

        with open(os.devnull, "w") as fnull:

            #print("Enabling Active Directory")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ActiveDirectory.Enable 1" % (dracname, drac_user, drac_pass), shell=True, stdout=fnull)

            #print("Configuring Standard Schema")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ActiveDirectory.Schema 2" % (dracname, drac_user, drac_pass), shell=True, stdout=fnull)

            #print("Configuring RAC Domain")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ActiveDirectory.RacDomain %s" % (dracname, drac_user, drac_pass, domain), shell=True, stdout=fnull)

            #print("Configuring User Domain")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.UserDomain.1.Name %s" % (dracname, drac_user, drac_pass, domain), shell=True, stdout=fnull)

            #print("Configuring Primary DRAC Group Name")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ADGroup.1.Name Development" % (dracname, drac_user, drac_pass), shell=True, stdout=fnull)

            #print("Configuring Primary DRAC Group Domain")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ADGroup.1.Domain %s" % (dracname, drac_user, drac_pass, domain), shell=True, stdout=fnull)

            #print("Configuring Primary DRAC Group Privilege")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ADGroup.1.Privilege 0x000000f9" % (dracname, drac_user, drac_pass), shell=True, stdout=fnull)

            #print("Configuring Domain Controller 1")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ActiveDirectory.DomainController1 10.26.160.31" % (dracname, drac_user, drac_pass), shell=True, stdout=fnull)

            #print("Configuring Domain Controller 2")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ActiveDirectory.DomainController1 10.26.160.32" % (dracname, drac_user, drac_pass), shell=True, stdout=fnull)

            #print("Configuring Lookup by User Domain")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ActiveDirectory.DCLookupByUserDomain 1" % (dracname, drac_user, drac_pass), shell=True, stdout=fnull)

            #print("Configuring Lookup domain name")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ActiveDirectory.DCLookupDomainName %s" % (dracname, drac_user, drac_pass, domain), shell=True, stdout=fnull)

            #print("Configuring Lookup Enable")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ActiveDirectory.GCLookupEnable 1" % (dracname, drac_user, drac_pass), shell=True, stdout=fnull)

            #print("Configuring AutoOSLockState to disabled")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.AutoOSLock.AutoOSLockState 0" % (dracname, drac_user, drac_pass), shell=True, stdout=fnull)

            #print("Configuring Root domain")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ActiveDirectory.GCRootDomain %s" % (dracname, drac_user, drac_pass, domain), shell=True, stdout=fnull)

        print("%s configuration has completed" % dracname)

    except urllib2.URLError as e:
        print("Error:", e)

threads = []
dracs = [line.rstrip() for line in open('servers.csv', 'r')] # line by line list of hostname-drac hosts
for host in dracs:
    t = threading.Thread(target=mainConfig, args=(host,))
    threads.append(t)
    t.start()

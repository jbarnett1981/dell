#!/usr/bin/python

'''
Created `03/27/2015 03:03`

@author jbarnett@tableausoftware.com
@version 0.2

dell_config.py: from csv, configure DRACs in parallel via threading module

TO DO:
- fix formatting to console (line break issues)
- add logging
'''

import socket
import subprocess
import csv
import os
import sys
import threading

drac_user = "root"
default_drac_pass = "PASSWORD"
drac_pass = "PASSWORD"
metacloud_user = "metacloud"
metacloud_pass = "PASSWORD"
domain="tsi.lan"

def get_ip(hostname):
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return 0

def exec_process(command):
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if err:
        print("failed: %s" % err)

commands = ["racadm %s -u %s -p %s set iDRAC.Security.CsrKeySize 2048",
 "racadm -r %s -u %s -p %s sslkeyupload -f drac.key -t 1",
 "racadm -r %s -u %s -p %s sslcertupload -f drac.pem -t 1"]

def main_config(oldname, newname):

    dracname = newname + "-drac"
    hostip = get_ip(oldname)
    if hostip != 0:
        sys.stdout.write("Configuring %s\n" % dracname)

        sys.stdout.write("Configuring root password\n")
        subprocess.call("racadm -r %s -u %s -p %s set iDRAC.Users.2.Password %s" % (hostip, drac_user, default_drac_pass, drac_pass), shell=True)

        if newname.lower().startswith("tsperf-"):
            sys.stdout.write("Enabling Active Directory")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ActiveDirectory.Enable 1" % (hostip, drac_user, drac_pass), shell=True)

            sys.stdout.write("Configuring Standard Schema")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ActiveDirectory.Schema 2" % (hostip, drac_user, drac_pass), shell=True)

            sys.stdout.write("Configuring RAC Domain")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ActiveDirectory.RacDomain %s" % (hostip, drac_user, drac_pass, domain), shell=True)

            sys.stdout.write("Configuring User Domain")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.UserDomain.1.Name %s" % (hostip, drac_user, drac_pass, domain), shell=True)

            sys.stdout.write("Configuring Primary DRAC Group Name")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ADGroup.1.Name Development" % (hostip, drac_user, drac_pass), shell=True)

            sys.stdout.write("Configuring Primary DRAC Group Domain")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ADGroup.1.Domain %s" % (hostip, drac_user, drac_pass, domain), shell=True)

            sys.stdout.write("Configuring Primary DRAC Group Privilege")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ADGroup.1.Privilege 0xf9" % (hostip, drac_user, drac_pass), shell=True)

            sys.stdout.write("Configuring Domain Controller 1")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ActiveDirectory.DomainController1 10.26.160.31" % (hostip, drac_user, drac_pass), shell=True)

            sys.stdout.write("Configuring Domain Controller 2")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ActiveDirectory.DomainController1 10.26.160.32" % (hostip, drac_user, drac_pass), shell=True)

            sys.stdout.write("Configuring Lookup by User Domain")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ActiveDirectory.DCLookupByUserDomain 1" % (hostip, drac_user, drac_pass), shell=True)

            sys.stdout.write("Configuring Lookup domain name")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ActiveDirectory.DCLookupDomainName %s" % (hostip, drac_user, drac_pass, domain), shell=True)

            sys.stdout.write("Configuring Lookup Enable")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ActiveDirectory.GCLookupEnable 1" % (hostip, drac_user, drac_pass), shell=True)

            sys.stdout.write("Configuring AutoOSLockState to disabled\n")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.AutoOSLock.AutoOSLockState 0" % (hostip, drac_user, drac_pass), shell=True)

            sys.stdout.write("Configuring Root domain\n")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.ActiveDirectory.GCRootDomain %s" % (hostip, drac_user, drac_pass, domain), shell=True)

        elif newname.lower().startswith("mhv"):

            sys.stdout.write("Configuring metacloud DRAC UserName \n")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.Users.3.UserName %s" % (hostip, drac_user, drac_pass, metacloud_user), shell=True)

            sys.stdout.write("Setting metacloud DRAC User Password\n")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.Users.3.Password %s" % (hostip, drac_user, drac_pass, metacloud_pass), shell=True)

            sys.stdout.write("Enabling metacloud DRAC User \n")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.Users.3.Enable 1" % (hostip, drac_user, drac_pass), shell=True)

            sys.stdout.write("Configuring metacloud DRAC user as iDRAC Administrator")
            subprocess.call("racadm -r %s -u %s -p %s set iDRAC.Users.3.Privilege 0x000001ff" % (hostip, drac_user, drac_pass), shell=True)

        sys.stdout.write("Enabling iDRAC DHCP\n")
        subprocess.call("racadm -r %s -u %s -p %s set iDRAC.IPv4.DHCPEnable Enabled" % (hostip, drac_user, drac_pass), shell=True)

        sys.stdout.write("Use DHCP to acquire DNS servers\n")
        subprocess.call("racadm -r %s -u %s -p %s set iDRAC.IPv4.DNSFromDHCP Enabled" % (hostip, drac_user, drac_pass), shell=True)

        sys.stdout.write("Register DRAC on DNS\n")
        subprocess.call("racadm -r %s -u %s -p %s set iDRAC.NIC.DNSRegister Enabled" % (hostip, drac_user, drac_pass), shell=True)

        sys.stdout.write("Configuring DNSRacName: %s\n" % dracname)
        subprocess.call("racadm -r %s -u %s -p %s set iDRAC.NIC.DNSRacName %s" % (hostip, drac_user, drac_pass, dracname), shell=True)

        sys.stdout.write("Auto Config Domain Name from DHCP\n")
        subprocess.call("racadm -r %s -u %s -p %s set iDRAC.NIC.DNSDomainNameFromDHCP Enabled" % (hostip, drac_user, drac_pass), shell=True)

        sys.stdout.write("Configuring System.LCD.LCDConfiguration to User Defined")
        subprocess.call("racadm -r %s -u %s -p %s set System.LCD.Configuration 0" % (hostip, drac_user, drac_pass), shell=True)

        sys.stdout.write("Configuring System.LCD.LCDUserString %s\n" % newname)
        subprocess.call("racadm -r %s -u %s -p %s set System.LCD.LCDUserString %s" % (hostip, drac_user, drac_pass, newname), shell=True)

        sys.stdout.write("Enabling IMPI over LAN\n")
        subprocess.call("racadm -r %s -u %s -p %s set iDRAC.IPMILan.Enable Enabled" % (hostip, drac_user, drac_pass), shell=True)

        sys.stdout.write("%s configuration has completed\n" % dracname)
    else:
        sys.stdout.write("%s not in DNS\n" % oldname)

threads = []
dracs = [line.rstrip() for line in open('servers.csv', 'r')] # comman delimited file in the format idrac-SERVICETAG.example.com,productionhostname
reader = csv.reader(dracs, delimiter=',')
for row in reader:
    oldname = row[0].strip().lower()
    newname = row[1].strip().lower()
    t = threading.Thread(target=main_config, args=(oldname, newname))
    threads.append(t)
    t.start()

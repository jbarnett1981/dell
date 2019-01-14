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
import os
import sys
import csv
import threading

drac_user = "root"
drac_pass = "PASSWORD"

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
		
commands = ["racadm -r %s -u %s -p %s set iDRAC.Security.CsrKeySize 2048",
 "racadm -r %s -u %s -p %s sslkeyupload -f drac.key -t 1",
 "racadm -r %s -u %s -p %s sslcertupload -f drac.pem -t 1"]

def main_config(dracname):
    hostip = get_ip(dracname)
    if hostip != 0:
        sys.stdout.write("Configuring %s (%s)\n" % (dracname, hostip))
        for command in commands:
            command = command % (hostip, drac_user, drac_pass)
            exec_process(command)
        drac_output = subprocess.Popen("racadm -r %s -u %s -p %s get iDRAC.Info.Type" % (hostip, drac_user, drac_pass), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = drac_output.communicate()
        if out.strip()[-2:] == "32":
            sys.stdout.write("%s is iDRAC8. Resetting DRAC manually...\n" % dracname)
            exec_process("racadm -r %s -u %s -p %s racreset" % (hostip, drac_user, drac_pass))
        sys.stdout.write("%s configuration has completed\n" % dracname)
    else:
        sys.stdout.write("%s not found in DNS\n" % dracname)
            
threads = []
dracs = [line.rstrip() for line in open('servers.csv', 'r')]
reader = csv.reader(dracs, delimiter=',')
for row in reader:
    dracname = row[1].strip().lower() + "-drac"
    t = threading.Thread(target=main_config, args=(dracname,))
    threads.append(t)
    t.start()

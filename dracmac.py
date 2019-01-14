#!/usr/bin/env python

'''
Created `05/06/2016 12:22`

@author jbarnett@tableau.com
@version 0.1

dracmac.py:

Script to dump the primary NICs MAC address on a Dell Server with onboard DRAC

changelog:

0.1
---
'''
import argparse
from rac import RAC
from colorama import Fore, Back, Style, init
import re

def printc(string, var):
    print(string + ":\t" + Fore.GREEN + var).expandtabs(12)

def get_args():
    '''
    Supports the command-line arguments listed below.
    '''
    parser = argparse.ArgumentParser(description='Process for retrieving MAC address from remote DRAC')

    credentials_parser = parser.add_argument_group('required login arguments')
    credentials_parser.add_argument('--username', required=True, help='username to authenticate to Remote DRAC')
    credentials_parser.add_argument('--password', required=True, help='password to authenticate to Remote DRAC')

    parser.add_argument('--hostname', required=True, help='IP or FQDN of remote DRAC to connect to')
    parser.add_argument('--cert', default=None, required=False, help='path to cert file')

    args = vars(parser.parse_args())

    return args

def main():
    ''' Main function '''

    args = get_args()

    pattern = '(NIC\.Integrated\.1-1-1)[a-zA-Z0-9\s=]{1,}([A-F0-9:]{17})'

    rac = RAC(args['hostname'], args['username'], args['password'])

    dump = rac.run_command('racdump')

    m = re.search(pattern, dump)

    mac_address = m.group(2)

    printc("MAC-NIC1", mac_address)


if __name__ == "__main__":
    main()
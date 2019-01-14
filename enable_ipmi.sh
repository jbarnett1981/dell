#!/bin/bash

while read line           
do           
    HOST=`echo -e "$line" | awk '{print $1}'`
    DRAC="$HOST-drac.tsi.lan"
    /usr/local/bin/racadm -H $DRAC -u root -p "PASSWORD" -c "config -g cfgIpmiLan -o cfgIpmiLanEnable 1"
done <build_servers.txt

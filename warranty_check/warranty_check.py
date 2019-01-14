#!/usr/bin/python

'''
Created `06/24/2015 12:20`

@author jbarnett@tableau.com
@version 0.7

warranty_add.py:

Adds warranty end date to hosts in racktables and sends HTML email report for warranties ending within 6 months to devit-inf@tableau.com.
Does external lookup via vendor APIs/web scraping.
Apple: from csv file produced by pyMacWarranty.py (https://github.com/pudquick/pyMacWarranty.git)
Dell: via warranty status API


changelog:

0.7
---
updated API key and endpoint to production after passing dell certification

0.6
---
separated script into:
1. checking for servers that have NULL warranty_end_date and update as necessary and
2. query all hosts to send out a report based on warranty_end date
added hardware sku syncing from warranty site to racktables (dell only)
html email list sorted by date in descending order
included sorted csv file as email attachment when specifying 'full' parameter

0.5
---
changed default apple/dell db query to use custom view tab_devit_custom_full
updated INSERT command for warranty end date to use ON DUPLICATE KEY UPDATE to not overwrite date if already exists

0.4
---
added hardware model syncing for Dell hardware
included hardware model column in html email report

0.3
---
fix path issues when being run from a different location or service (i.e via cron)

0.2
---
added hardware type and date to jinja HTML template
added alternating row colors for jinja HTML template

todo:

add totals count to HTML report
logging errors, output to error file
exception handling
separate HTML report into "already expired", "upcoming expirations"

'''


import pymysql
import subprocess
import csv
import json
import argparse
import jinja2
import os
import sys
from urllib2 import urlopen
from time import time, mktime, strptime, sleep
from datetime import datetime, timedelta
import email, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def asset_dump(db, query_type):
    """
    Return list of devit hardware serial numbers from Racktables DB
    """
    cur = db.cursor()
    if query_type == 'apple':
        cur.execute("""select serial_no from tab_devit_custom_full where hw_type like 'apple%' and warranty_end_date is NULL""")
    elif query_type == 'dell':
        cur.execute("""select serial_no from tab_devit_custom_full where hw_type like 'dell%' and warranty_end_date is NULL""")
    elif query_type == 'full':
        cur.execute("""select * from tab_devit_custom_full where warranty_end_date is not NULL""")
    db_dump = cur.fetchall()
    #close cursor
    cur.close()
    return db_dump

def add_obj_attrs(db, obj_id, hostname, warranty_end_date, order_info=False):
    '''
    Adds warranty end date attribute to host with specified id
    '''
    cur = db.cursor()
    cur.execute("""insert into AttributeValue (object_id, object_tid, attr_id, string_value, uint_value, float_value) values (%s,4,21,NULL,%s,NULL) on duplicate key update object_id=object_id""", (obj_id, warranty_end_date))
    if order_info:
        cur.execute("""update RackObject set comment=%s where id=%s""", (order_info, obj_id))
        print("Added Sales Order data for %s" % hostname)
    print("Added Warranty End Date for %s" % hostname)
    #actually commit changes to database and close cursor
    db.commit()
    cur.close()

def get_host_info(db, serial_no):
    '''
    Returns the object hostname for a given serial number.
    '''
    cur = db.cursor()
    cur.execute("""select id, name from tab_devit_custom_full where serial_no=%s""", serial_no)
    host_info = cur.fetchone()
    cur.close()
    return host_info

def update_server_type(db, obj_id, hostname, server_sku):
    '''
    Returns server type for given object id and updates it if empty
    '''
    try:
        #get server sku id
        sku_id = get_sku_id(db, server_sku)
        cur = db.cursor()
        cur.execute("""select uint_value from AttributeValue where object_id=%s and attr_id=2""", obj_id)
        racktables_sku = cur.fetchone()
        if not racktables_sku:
            cur.execute("""insert into AttributeValue (object_id, object_tid, attr_id, string_value, uint_value, float_value) values (%s,4,2,NULL,%s,NULL)""", (obj_id, sku_id))
            print("Added Server Model for %s" % hostname)
        else:
            print("Server Model already exists for %s: %s" % (hostname, server_sku))
        #actually commit changes to database and close cursor
        db.commit()
        cur.close()
    except TypeError:
        print("Server SKU from Dell Warranty API did not find a match in Racktables DB")

def get_sku_id(db, server_sku):
    '''
    Returns server model id (dict_key) from Racktables associated with string value server model
    '''
    cur = db.cursor()
    cur.execute("""select dict_key from Dictionary where chapter_id=11 and dict_value like '%{0}'""".format(server_sku[-4:]))
    sku_id = cur.fetchone()[0]
    return sku_id

def send_email(msg, attachment):
    """
    Send email message of warranty report
    """
    html_msg = MIMEText(msg, 'html')
    f = file(attachment)
    attach = MIMEText(f.read())
    attach.add_header('Content-Disposition', 'attachment', filename=attachment)

    msg = MIMEMultipart()
    #msg['To'] = 'devit-inf@tableau.com'
    msg['To'] = 'jbarnett@tableau.com'
    msg['From'] = "jbarnett@tableau.com"
    msg['Subject'] = "Hardware Warranty End Dates < 6 months"
    msg['Date'] = datetime.now().strftime("%d %b %Y %H:%M:%S -0700")
    msg.attach(html_msg)
    msg.attach(attach)

    srv = smtplib.SMTP('smarthost.tsi.lan')
    srv.sendmail(msg['From'], msg['To'], msg.as_string())
    srv.quit()

def usage():
    '''argparse usage function'''
    # Command line parameters via argparse.
    parser = argparse.ArgumentParser(description='%(prog)s help')
    #parser.add_argument("-d", "--debug", required=False, action="store_true", help="print debug messages to stdout")
    parser.add_argument("--version", action="version", version="%(prog)s 0.5")
    subparsers = parser.add_subparsers()

    parser_query = subparsers.add_parser('sync', help='sync warranty date info for Apple or Dell hardware to racktables', formatter_class=argparse.RawDescriptionHelpFormatter, epilog="syntax:\nwarranty_check sync --apple\nwarranty_check sync --dell")
    group_query = parser_query.add_mutually_exclusive_group(required=True)
    group_query.set_defaults(which='sync')
    group_query.add_argument("--apple", action="store_true", help="sync warranty information for Apple servers")
    group_query.add_argument("--dell", action="store_true", help="sync warranty information for Dell servers")

    parser.full = subparsers.add_parser('full', help='dump full list of hardware and warranty end dates to generate report for warranty renewal planning', formatter_class=argparse.RawDescriptionHelpFormatter, epilog="syntax:\nwarranty_check --full")
    parser.full.set_defaults(which='full')

    args = vars(parser.parse_args())
    return args

def main():

    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

    args = usage()

    #collect credentials from config file
    config_file = os.path.join(__location__, "config/creds.json")
    cred_data = json.loads(open(config_file).read())
    rtables_host = cred_data['racktables']['server']
    rtables_db_user = cred_data['racktables']['db_user']
    rtables_db_pass = cred_data['racktables']['db_pass']
    rtables_db = cred_data['racktables']['db']

    if args['which'] == 'sync':

        #open connection to racktables db
        db = pymysql.connect(host=rtables_host, user=rtables_db_user, passwd=rtables_db_pass, db=rtables_db)

        if args['apple']:

            query_type = 'apple'

            # db_dump = asset_dump(db, query_type)
            # serial_numbers = [num[0] for num in db_dump]
            # serials_file = ''.join([os.path.join(__location__, ''.join(['apple_serials-',datetime.now().strftime("%m%d%Y"),'.txt']))])
            # with open(serials_file, 'wb') as myfile:
            #     for serial in serial_numbers:
            #         myfile.write(serial + "\n")

            # #create warranty csv file from pyMacWarranty.py
            # warranty_file = ''.join([os.path.join(__location__, ''.join(['warranty-',datetime.now().strftime("%m%d%Y"),'.txt']))])
            # subprocess.call(['/usr/bin/python %s/pyMacWarranty/getwarranty.py -f %s -c -o %s' % (__location__, serials_file, warranty_file)], shell=True)

            # f = open(warranty_file, "r")
            # reader = csv.reader(f, delimiter=',')
            # reader.next() #skip first commented header row
            # items = []
            # for row in reader:
            #     serial_no = row[0]
            #     warranty_end_date = row[9]
            #     epoch_time = int(mktime(strptime(warranty_end_date, '%Y-%m-%d')))
            #     hostid, hostname = get_host_info(db, serial_no)
            #     #add warranty end date to racktables, or update if it already exists.
            #     add_obj_attrs(db, hostid, hostname, epoch_time)

            # #close file connection
            # f.close()
            f = open('Tableau_apple.csv', "r")
            reader = csv.reader(f, delimiter=',')
            reader.next() #skip first commented header row
            for row in reader:
                sales_order = "Sales Order: " + row[1]
                serial_no = row[5]
                warranty_end_date = row[9]
                epoch_time = int(mktime(strptime(warranty_end_date, '%m/%d/%y')))
                hostid, hostname = get_host_info(db, serial_no)
                print(hostname)
                #add warranty end date to racktables, or update if it already exists.
                add_obj_attrs(db, hostid, hostname, epoch_time, sales_order)


        if args['dell']:

            query_type = 'dell'

            apikey = '7156efc907cde60a9feaac8701367170'
            base_url = 'https://apidp.dell.com/support/assetinfo/v4/getassetwarranty/%s?apikey=%s'

            db_dump = asset_dump(db, query_type)
            if db_dump:
                serial_numbers = [num[0] for num in db_dump]
                serials_file = ''.join([os.path.join(__location__, ''.join(['dell_serials-',datetime.now().strftime("%m%d%Y"),'.txt']))])
                with open(serials_file, 'wb') as myfile:
                    for serial in serial_numbers:
                        myfile.write(serial + "\n")

                items = []

                for sn in serial_numbers:
                    #extended_dates = []
                    api_url = base_url % (sn, apikey)
                    json_data = json.load(urlopen(api_url))
                    #not used currently but need to implement
                    try:
                        server_sku = json_data['AssetWarrantyResponse'][0]['AssetHeaderData']['MachineDescription']
                        # for dicts in json_data['AssetWarrantyResponse'][0]['AssetEntitlementData']:
                        #     if dicts['ServiceLevelCode'] == 'ND' or dicts['ServiceLevelCode'] == 'S1':
                        #         extended_dates.append(dicts['EndDate'])
                        # max_date = max(extended_dates)
                        end_date = json_data['AssetWarrantyResponse'][0]['AssetEntitlementData'][0]['EndDate']
                        warranty_end_date = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S")
                        print("Serial Number: %s\tEnd Date: %s" %(sn, warranty_end_date))
                        epoch_time = (warranty_end_date - datetime(1970,1,1)).total_seconds() + 86400
                        hostid, hostname = get_host_info(db, sn)
                        #add warranty end date to racktables, or update if it already exists.
                        add_obj_attrs(db, hostid, hostname, epoch_time)
                        #check/update server sku if necessary
                        update_server_type(db, hostid, hostname, server_sku)
                        sleep(1)
                    except IndexError as e:
                        print("Invalid data %s" % e)
            else:
                sys.exit("Nothing to update")
        #close connection to racktables db
        db.close()

    if args['which'] == 'full':

        #open connection to racktables db
        db = pymysql.connect(host=rtables_host, user=rtables_db_user, passwd=rtables_db_pass, db=rtables_db)

        query_type = 'full'

        #get datetime object 6 months from now.
        six_months_from_now = datetime.now() + timedelta(6*365/12)

        #obtain dump from db of all assets
        asset_list = asset_dump(db, query_type)

        #intialize empty list to be used for jinja template
        items = []

        for asset in asset_list:
            (asset_id, asset_name, asset_hw_type, asset_serial, asset_end_date) = asset
            #convert epoch time from racktables db to datetime object for comparison
            warranty_end_date = datetime.fromtimestamp(asset_end_date)
            #determine if warranty is expiring within 6 months and add to dict
            if warranty_end_date < six_months_from_now:
                item = dict(name=asset_name.lower(), serial_no=asset_serial.upper(), server_model=asset_hw_type, date=warranty_end_date)
                items.append(item)

        #sort list in descending order
        sorted_items = sorted(items, key=lambda k: k['date'], reverse=True)

        #create csv file to attach to email from sorted_items
        dict_keys = sorted_items[0].keys()
        today = datetime.now().strftime("%m%d%y")
        attachment = 'warranty_end_dates_' + today + '.csv'
        with open(attachment, 'wb') as f:
            csv_writer = csv.DictWriter(f, dict_keys)
            csv_writer.writeheader()
            csv_writer.writerows(sorted_items)

        #load and render template
        loader = jinja2.FileSystemLoader(os.path.join(__location__, 'templates'))
        env = jinja2.Environment(loader=loader)
        template = env.get_template('report_template.html')
        today = datetime.now().strftime("%m-%d-%Y")
        total = len(items)
        title = "Warranty End Dates"
        msg = template.render(items=sorted_items, title=title, today=today, total=total)
        #send template in email msg
        send_email(msg, attachment)

if __name__ == "__main__":
    main()

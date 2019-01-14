warranty_check 0.1
=====
author: Julian Barnett // jbarnett@tableau.com

warranty_check.py: dumps bare metal server serial numbers from Racktables DB, then verifies warranty information with specific vendor and populates back into Racktables. Also generates HTML email report listing hosts nearing EOL < 6 months

Pre-Requisites: 

You must install the following modules (available via pip). Script will fail without these:
python-dateutil (pip install python-dateutil)
jinja2 (pip install jinja2)
pymysql (pip install pymysql)

Manage credentials and server details via ./config/creds.json. Update this with your info.

```
{"racktables": {
        "server": "racktables.dev.tsi.lan",
        "db_user": "<in KeePass>",
        "db_pass": "<in KeePass>",
        "db": "racktables_db"
    }
}
```

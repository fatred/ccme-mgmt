#!/usr/local/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""
	A Simple CCME Query Script

Author: John Howard <fatred+ccmeapp@gmail.com>

"""
from ciscoconfparse import CiscoConfParse
from config import Config
import getpass
import paramiko
import time
import re
import sqlite3
import sys, traceback

# basics
# use basic config file mgmt
cfg_file = file('ccme_server.cfg')
ccme_config = Config(cfg_file)

# we need to talk to a CCME box obvs.
ccme_addr = ccme_config.ccme_server_addr
ccme_port = ccme_config.ccme_server_port

# we need username and passwords
# get username
default_username = getpass.getuser()
username = raw_input('[*] Username [%s]: ' % default_username)
if not username:
    username = default_username

# get password
password = getpass.getpass("[*] Password: ")

# debug mode?
debug = ccme_config.debug
# connect to the ccme
try: 
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print('[*] Connecting to %s...') % ccme_addr
    client.connect(ccme_addr, ccme_port, username, password)
    
    # hopefully that worked
    session = client.invoke_shell()
    if debug:
        print(repr(client.get_transport()))
        check_prompt = session.recv(1000)
        print(check_prompt)
    # now we are online and running at the shell...
    # disable paging in the session for config gathering.
    session.send("terminal length 0\n")
    time.sleep(1)
    if debug: 
        check_output = session.recv(1000)
        print(check_output)
    
    # pull the config back to a big-ish buffer
    session.send("sh run\n")
    time.sleep(10)
    ccme_raw_config = session.recv(512000)
    if debug:
        print('---- RAW CONFIG ----')
        print(ccme_raw_config)
        print('---- END CONFIG ----')
    
    # parse that raw test into a string
    conf_string = str(ccme_raw_config).splitlines()
    
    # parse that text into a CiscoConfParse Object
    cisco_conf = CiscoConfParse(conf_string)
    
    # prove it worked
    ccme_hostname = cisco_conf.find_objects(r"^hostname")[0].text[9:]
    ccme_version = cisco_conf.find_objects(r"^version")[0].text[-4:]
    handsets = cisco_conf.find_objects(r'^ephone ')
    dirnums = cisco_conf.find_objects(r'^ephone-dn ')
    print("[*] Config Parsed: %s | %s") % (ccme_hostname, ccme_version)
    print("[*] %s handsets | %s dir nums") % (len(handsets), len(dirnums))
    
    
    print "[*] Connecting to Database ccme-mgmt"
    db = sqlite3.connect('ccme-mgmt.sqlite')
    cur = db.cursor()
    
    print "[*] Checking to see if Database has entries or not..."
    if cur.execute('select count(*) from sqlite_master where type = "table"').fetchone() == (0,):
        print "[W] Database is empty - deploying schema"
        schema_sql = open('ccme-mgmt.sql', 'r').read()
        populate_schema = cur.executescript(schema_sql)
        if cur.execute('select count(*) from sqlite_master where type = "table"').fetchone() == (0,):
            print "[E] Error importing Schema - check schema file"
            os._exit(1)
        print "[*] Schema imported ok!"
        
    print "[*] Importing handsets into Database"
    for handset in handsets:
        # ephone number
        ephone_id = re.search(re.compile(ur'ephone\s*(\d*)'), str(handset.ioscfg))
        # description 
        desc = re.search(re.compile(ur'\s+description\s+([^\']+)'), str(handset.ioscfg))
        # mac address
        mac_addr = re.search(re.compile(ur'\smac-address\s*(\w{4}\.\w{4}\.\w{4})'), str(handset.ioscfg))
        # type
        type_num = re.search(re.compile(ur'\s+type\s+([^\'])'), str(handset.ioscfg))
        # button
        button_num = re.search(re.compile(ur'\s+button\s+\d\:([^\']+)'), str(handset.ioscfg))
        # ephone-templ
        templ_num = re.search(re.compile(ur'\s+ephone-template\s+([^\']+)'), str(handset.ioscfg))
        
        
        # cur.execute('INSERT OR REPLACE INTO handsets (ephone_id) VALUES (?)', ephone_id.group(1)) 
        #cur.execute('INSERT OR REPLACE INTO handsets (ephone_id,desc) VALUES (?,?)', (ephone_id.group(1), desc.group(1)))
        
        if not ephone_id:
            print "[E] No ephone number found in record"
            break
        
        if not desc:
            desc_value = "none"
        else: 
            desc_value = desc.group(1)
        
        if not mac_addr:
            print "[E] No MAC Address on ephone %s" % ephone_id.group(1)
            pass
        
        if not type_num:
            print "[W] No Type provided for ephone %s, default to 7911" % ephone_id.group(1)
        
        if not button_num:
            print "[W] No Dirnum button assigned to ephone %s" % ephone_id.group(1)
        
        if not templ_num:
            print "[W] No ephone template on ephone %s" % ephone_id.group(1)
            templ_value = ""
        else: 
            templ_value = templ_num.group(1)

        cur.execute('INSERT OR REPLACE INTO handsets (ephone_id, desc, "mac-address", type, button, "ephone-template") VALUES (?,?,?,?,?,?)', (ephone_id.group(1), desc_value, mac_addr.group(1), type_num.group(1), button_num.group(1), templ_value))
        # be shouty
        print "[*] Added ephone %s|%s to Database!" % (ephone_id.group(1), mac_addr.group(1))
    
    # commit data to db
    cur.commit()

    # cleanup
    session.close()
    client.close()

except Exception as e:
    print('[E] Caught exception: %s: %s' % (e.__class__, e))
    traceback.print_exc()
    try:
        client.close()
    except:
        pass
    sys.exit(1)


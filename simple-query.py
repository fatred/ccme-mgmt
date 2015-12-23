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
    
    """
        regexing the handsets
        ephone num
            cur.execute('INSERT OR REPLACE INTO handsets (ephone_id, desc, "mac-address", "ephone-template", type, button) VALUES (999, "horse", "1111.2222.3333", 1, 7911, 12)')
            print "ephone num %s" % re.search(re.compile(ur'^ephone\s*(\d*)$'), handset.ioscfg[0]).group(1)
            print "mac addr %s" % re.search(re.compile(ur'\smac-address\s*(\w{4}\.\w{4}\.\w{4})'), str(handsets[20].ioscfg)).group(1)
    """
    
    print "[*] Connecting to Database ccme-mgmt"
    db = sqlite3.connect('ccme-mgmt.sqlite')
    cur = db.cursor()
    
    print "[*] Importing handsets into Database"
    for handset in handsets:
        # ephone number
        ephone_id = re.search(re.compile(ur'ephone\s*(\d*)'), str(handset.ioscfg))
        if ephone_id:
            cur.execute('INSERT OR REPLACE INTO handsets (ephone_id) VALUES (?)', ephone_id.group(1)) 
        else:
            print "[E] No ephone number found in record"
            break
        # description 
        desc = re.search(re.compile(ur'\s+description\s+([^\']+)'), str(handset.ioscfg))
        if desc:
            cur.execute('INSERT OR REPLACE INTO handsets (ephone_id,desc) VALUES (?,?)', (ephone_id.group(1), desc.group(1)))
        else:
            cur.execute('INSERT OR REPLACE INTO handsets (ephone_id,desc) VALUES (?,?)', (ephone_id.group(1), "none"))
        # mac address
        mac_addr = re.search(re.compile(ur'\smac-address\s*(\w{4}\.\w{4}\.\w{4})'), str(handset.ioscfg))
        if mac_addr:
            cur.execute('INSERT OR REPLACE INTO handsets (ephone_id,"mac-address") VALUES (?,?)', (ephone_id.group(1)), mac_addr.group(1))
        else:
            print "[E] No MAC Address on ephone %s" % ephone_id.group(1)
            break
        # type
        type_num = re.search(re.compile(ur'\s+type\s+([^\'])'), str(handset.ioscfg))
        if type_num:
            cur.execute('INSERT OR REPLACE INTO handsets (ephone_id,type) VALUES (?,?)', (ephone_id.group(1), type_num.group(1)))
        else:
            print "[W] No Type provided for ephone %s, default to 7911" % ephone_id.group(1)
        # button
        button_num = re.search(re.compile(ur'\s+button\s+\d\:([^\']+)'), str(handset.ioscfg))
        if button_num:
            cur.execute('INSERT OR REPLACE INTO handsets (ephone_id,button) VALUES (?,?)', (ephone_id.group(1), button_num.group(1)))
        else:
            print "[W] No Dirnum button assigned to ephone %s" % ephone_id.group(1)
        # ephone-templ
        templ_num = re.search(re.compile(ur'\s+ephone-template\s+([^\']+)'), str(handset.ioscfg))
        if templ_num:
            cur.execute('INSERT OR REPLACE INTO handsets (ephone_id,"ephone-template") VALUES (?,?)', (ephone_id.group(1), templ_num.group(1)))
        else:
            print "[W] No ephone template on ephone %s" % ephone_id.group(1)
        
        # be shouty
        print "[*] Added ephone %s|%s to Database!" % (ephone_id.group(1), mac_addr.group(1))

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


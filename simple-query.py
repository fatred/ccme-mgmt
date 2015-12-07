from ciscoconfparse import CiscoConfParse
import getpass
import paramiko
import time

debug = True
# basics
# we need to talk to a CCME box obvs.
ccme_addr = raw_input('CCME Server IP: ')
ccme_port = 22022

# we need username and passwords
# get username
default_username = getpass.getuser()
username = raw_input('Username [%s]: ' % default_username)
if not username:
    username = default_username

# get password
password = getpass.getpass("Password: ")

# connect to the ccme
try: 
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.WarningPolicy())
    print('Connecting...')
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
    print("\tConfig Parsed: %s: | %s") % (ccme_hostname, ccme_version)

    # cleanup
    session.close()
    client.close()

except Exception as e:
    print('*** Caught exception: %s: %s' % (e.__class__, e))
    traceback.print_exc()
    try:
        client.close()
    except:
        pass
    sys.exit(1)


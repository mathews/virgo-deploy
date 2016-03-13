## -*- coding: utf-8 -*-
"""
Created on Sat Feb 20 00:32:38 2016

@author: mathews
"""

import paramiko
import sys

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #client.load_system_host_keys()
    #client.set_missing_host_key_policy(paramiko.WarningPolicy())
    print('*** Connecting...')

    #client.connect('127.0.0.1',  username='karaf', password='karaf',port = 8101)
    client.connect('127.0.0.1',  username='admin', password='springsource',port = 2502)
    #client.connect('127.0.0.1',  username='admin', password='admin',port = 8000)
    #client.connect('192.168.1.144',  username='stack', password='active123',port = 22)
    #chan = client.open_session()

    print('*** Connected...')
    (stdin, stdout, stderr) = client.exec_command('log:display')

    print stdout.readlines()

    #chan.close()
    client.close()

except Exception as e:
    print('*** Caught exception: %s: %s' % (e.__class__, e))
    try:
        client.close()
    except:
        pass
    sys.exit(1)
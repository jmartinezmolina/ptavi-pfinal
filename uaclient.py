#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
import uaserver
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import os
import time


if len(sys.argv) != 4:    
    sys.exit("Usage: python uaclient.py config method option")

Config = sys.argv[1]
parser = make_parser()
cHandler = uaserver.XMLHandler()
parser.setContentHandler(cHandler)

try:
    parser.parse(open(Config))
except:
    sys.exit("Usage: python uaclient.py config method option")

Method = sys.argv[2]
fich_xml = cHandler.get_tags()
Log = open(fich_xml[4]["path"], "a")
SERVER = fich_xml[3]["pr_ip"]
PORT = int(fich_xml[3]["pr_port"])
Options = sys.argv[3]
LogSent = " Sent to " + str(SERVER) + ":" + str(PORT) + ": "
LogRec = " Received from " + str(SERVER) + ":" + str(PORT) + ": "
my_name = fich_xml[0]["name"]
if Method == "REGISTER":

    Log.write(time.strftime('%Y­%m­%d%H%M%S') + " Starting...\r\n")
    Line = "REGISTER sip:" + my_name + ":" + fich_xml[1]["serv_port"] + \
    " SIP/2.0\r\n" + "Expires: " + Options + "\r\n"
    Log.write(time.strftime('%Y­%m­%d%H%M%S') + LogSent + "REGISTER "+ ("\r\n"))
elif Method == "INVITE":
    Line = "INVITE sip:" + Options + " SIP/2.0\r\n" + \
    "Content-Type: application/sdp\r\n\r\nv=0\r\no=" + fich_xml[0]["name"] + \
    " " + fich_xml[1]["serv_ip"] + "\r\ns=misesion\r\nt=0\r\nm=audio " + fich_xml[2]["rtp_port"] + " RTP"
    Log.write(time.strftime('%Y­%m­%d%H%M%S') + LogSent +"INVITE " + Options + "\r\n")
elif Method == "BYE":
    Line = "BYE sip:" + Options + " SIP/2.0\r\n"
    Log.write(time.strftime('%Y­%m­%d%H%M%S') + LogSent +"BYE " + Options + "\r\n")
    Log.write(time.strftime('%Y­%m­%d%H%M%S') + "Finishing." + "\r\n")
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((SERVER, PORT))
my_socket.send(Line + '\r\n')
data = my_socket.recv(1024)
print data   
data = data.split("\r\n")
if "SIP/2.0 200 OK" in data and Method == "INVITE":
    name = data[6].split(" ")[0][2:]
    Ip = data[6].split(" ")[1]
    port =data[9].split(" ")[1]
    fich_audio = fich_xml[5]["path"]
    aEjecutar = ('./mp32rtp -i ' + Ip + ' -p '+ port + ' < ' + \
                    fich_audio)
    print "EJECUTO Mp32rtp", aEjecutar
    os.system(aEjecutar)
    Line = "ACK" + " sip:" + name + " SIP/2.0"
    my_socket.send(Line + '\r\n')
    Log.write(time.strftime('%Y­%m­%d%H%M%S') + LogSent +"ACK " + Options + "\r\n")
if "SIP/2.0 200 OK" in data:
    Log.write(time.strftime('%Y­%m­%d%H%M%S') + LogRec + "200 OK\r\n")
if "SIP/2.0 404 User Not Found" in data:
    Log.write(time.strftime('%Y­%m­%d%H%M%S') + LogRec + "404 user Not Found\r\n")
Log.close()

#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import time
import SocketServer
import sys
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class XMLHandler(ContentHandler):

    def __init__(self):
        self.List = []

    def startElement(self, name, attrs):

        if name == "account":

            self.account = {}
            self.account["name"] = attrs.get("name", "")
            self.List.append(self.account)

        elif name == "uaserver":

            self.uaserver = {}
            self.uaserver["serv_ip"] = attrs.get("serv_ip", "")
            self.uaserver["serv_port"] = attrs.get("serv_port", "")
            self.List.append(self.uaserver)

        elif name == "rtpaudio":

            self.rtpaudio = {}
            self.rtpaudio['rtp_port'] = attrs.get("rtp_port", "")
            self.List.append(self.rtpaudio)

        elif name == "regproxy":

            self.regproxy = {}
            self.regproxy["pr_ip"] = attrs.get("pr_ip", "")
            self.regproxy["pr_port"] = attrs.get("pr_port", "")
            self.List.append(self.regproxy)

        elif name == "log":

            self.log = {}
            self.log["path"] = attrs.get("path", "")
            self.List.append(self.log)
        elif name == "audio":

            self.audio = {}
            self.audio["path"] = attrs.get("path", "")
            self.List.append(self.audio)

    def get_tags(self):
        return self.List


class EchoHandler(SocketServer.DatagramRequestHandler):
    """
    Echo server class
    """

    def handle(self):

        while 1:
            line = self.rfile.read()
            if not line:
                break
            print  line
            line = line.split(" ")
            method = line[0]

            if method == "INVITE":

                self.wfile.write("SIP/2.0 100 Trying\r\n")
                self.wfile.write("SIP/2.0 180 Ring\r\n")
                self.wfile.write("SIP/2.0 200 OK\r\n")
                self.wfile.write("Content-Type: application/sdp\r\n\r\n")
                self.wfile.write("v=0\r\n")
                Dir = fich_xml[1]["serv_ip"]
                port_rtp = fich_xml[2]["rtp_port"]
                self.wfile.write("o=" + fich_xml[0]["name"] + " " + Dir + "\r\n")
                self.wfile.write("s=sesionamigo\r\n")
                self.wfile.write("t=0\r\n")
                self.wfile.write("m=audio " + port_rtp + " RTP\r\n")
                IP_rtp = line[4].split("\r\n")[0]
                port = line[5]
                name = line[3].split("\r\n")[3][2:]
                Dir_rtp = [IP_rtp, port]
                SDP[name] = Dir_rtp
            elif method == "ACK":               
                for user in SDP:
                    Dir_rtp = SDP[user]
                    fich_audio = fich_xml[5]["path"]
                    aEjecutar = ('./mp32rtp -i ' + Dir_rtp[0] + ' -p ' + Dir_rtp[1] + ' < ' + \
                    fich_audio)
                    print "EJECUTO Mp32rtp", aEjecutar
                    os.system(aEjecutar)
            elif method == "BYE":
                self.wfile.write("SIP/2.0 200 OK\r\n")
            else:
                self.wfile.write("SIP/2.0 405 Method Not Allowed\r\n")

            Log = open(fich_xml[4]["path"], "a")
            if method == "INVITE":
                Log.write(time.strftime('%Y­%m­%d%H%M%S') + " Received from " + name + ": " + method + ("\r\n"))
                Log.write(time.strftime('%Y­%m­%d%H%M%S') + " Sent to " + name + ": " + "SIP/2.0 200 OK\r\n")
            elif method == "ACK":
                Log.write(time.strftime('%Y­%m­%d%H%M%S') + " Received : " + method + ("\r\n"))
            elif  method == "BYE":
                Log.write(time.strftime('%Y­%m­%d%H%M%S') + " Received : " + method + ("\r\n"))
                Log.write(time.strftime('%Y­%m­%d%H%M%S') + " Sent : " + "SIP/2.0 200 OK\r\n")
            else:
                Log.write(time.strftime('%Y­%m­%d%H%M%S') + " Sent : " + "SIP/2.0 405 Method Not Allowed\r\n")
            Log.close()
if __name__ == "__main__":
    # Creamos servidor de eco y escuchamos
    
    config = sys.argv[1]
    parser = make_parser()
    cHandler = XMLHandler()
    parser.setContentHandler(cHandler)
    try:
        parser.parse(open(config))
    except:
        sys.exit("Usage: python uaserver.py config")
    fich_xml = cHandler.get_tags()
    Dir = fich_xml[1]
    serv = SocketServer.UDPServer((Dir["serv_ip"], int(Dir["serv_port"])), EchoHandler)
    SDP = {}
    print "Listening...."
    serv.serve_forever()

#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa servido que gestiona el registro y caduciadad de los usuarios
"""

import SocketServer
import sys
import time
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import uaserver

import socket


class XMLHandler(ContentHandler):
    def __init__(self):
        self.List = []

    def startElement(self, name, attrs):

        if name == "server":
            self.server = {}
            self.server["name"] = attrs.get("name", "")
            self.server["ip"] = attrs.get("ip", "")
            self.server["port"] = attrs.get("port", "")
            self.List.append(self.server)

        elif name == "database":
            self.database = {}
            self.database["path"] = attrs.get("path", "")
            self.List.append(self.database)

        elif name == "log":
            self.log = {}
            self.log["path"] = attrs.get("path", "")
            self.List.append(self.log)

    def get_tags(self):
        return self.List


class SIPRegisterHandler(SocketServer.DatagramRequestHandler):
    """
    SIP server class
    """
    List_Client = {}

    def handle(self):
        """
        Gestiona el mensaje que entra y el registro de los usurios
        """
        for user in self.List_Client.keys():
            if self.List_Client[user][1] < time.time():
                del self.List_Client[user]
        while 1:
            line = self.rfile.read()
            if not line:
                break
            msg = line
            print msg
            line = line.split()
            Method = line[0]
            if Method == "REGISTER":
                name = line[1].split(":")[1]
                print name
                port = line[1].split(":")[2]
                print port
                if line[4] == "0":
                    if name in self.List_Client:
                        del self.List_Client[name]
                else:
                    self.List_Client[name] =\
                        (self.client_address[0], port,
                         time.time()+float(line[4]))
                self.register2file()
                self.wfile.write("SIP/2.0 200 OK\r\n\r\n")
            elif Method == "INVITE":
                name = line[6][2:]
                send = 0
                for user in self.List_Client.keys():
                    if user == name:
                        call = line[1][4:]
                        for inv in self.List_Client.keys():
                            if inv == call:
                                my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                                my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                                my_socket.connect((self.List_Client[call][0], int(self.List_Client[call][1])))
                                my_socket.send(msg)
                                data = my_socket.recv(1024)
                                print data
                                my_socket.close()
                                self.wfile.write(data)
                                send = 1
                        if send == 0:
                            self.wfile.write("SIP/2.0 404 User Not Found\r\n")
            elif Method == "ACK":
                name = line[1][4:]
                send = 0
                for inv in self.List_Client.keys():
                    if inv == name:
                        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        my_socket.connect((self.List_Client[name][0], int(self.List_Client[name][1])))
                        my_socket.send(msg)
                        data = my_socket.recv(1024)
                        print data
                        my_socket.close()
                        self.wfile.write(data)
                        send = 1
                if send == 0:
                    self.wfile.write("SIP/2.0 404 User Not Found\r\n")
            elif Method == "BYE":
                name = line[1][4:]
                send = 0
                for inv in self.List_Client.keys():
                    if inv == name:
                        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        my_socket.connect((self.List_Client[name][0], int(self.List_Client[name][1])))
                        my_socket.send(msg)
                        data = my_socket.recv(1024)
                        print data
                        my_socket.close()
                        self.wfile.write(data)
                        send = 1
                if send == 0:
                    self.wfile.write("SIP/2.0 404 User Not Found\r\n")

            Log = open(fich_xml[2]["path"], "a")
            Log.write(time.strftime('%Y­%m­%d%H%M%S') + " Received from " + name + ": " + Method + ("\r\n"))
            if send == 0 and Method != "REGISTER":
                Log.write(time.strftime('%Y­%m­%d%H%M%S') + " Sent to " + name + ": " + "SIP/2.0 404 User Not Found\r\n") 			

            elif send == 1 and Method != "REGISTER":
                Log.write(time.strftime('%Y­%m­%d%H%M%S') + " Sent to " + name + ": " + "SIP/2.0 200 OK\r\n")

    def register2file(self):
        """
        Guarda en un fichero el diccionario de clientes
        """
        fich = open(fich_xml[1]["path"], 'w')
        line = ("Use" + "\t" + "IP" + "\t" + "Expires" + "\r\n")
        for user in self.List_Client.keys():
            h_Expires = time.strftime('%Y-%m-%d %H:%M:%S',
                                      time.gmtime(self.List_Client[user][2]))
            line += user + "\t" + self.List_Client[user][0] + "\t" + h_Expires + "\r\n"
        fich.write(line)
        fich.close()

if __name__ == "__main__":
    # Creamos servidor de eco y escuchamos

    if len(sys.argv) != 2:
      sys.exit("Usage: python proxy_registrar.py config")
    config = sys.argv[1]
    parser = make_parser()
    cHandler = XMLHandler()
    parser.setContentHandler(cHandler)
    try:
        parser.parse(open(config))
    except:
        sys.exit("Usage: python proxy_registrar.py config")

    fich_xml = cHandler.get_tags()
    Log = open(fich_xml[2]["path"], "a")
    Dir = fich_xml[0]
    serv = SocketServer.UDPServer((Dir["ip"], int(Dir["port"])), SIPRegisterHandler)
    serv.serve_forever()

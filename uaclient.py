#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# Práctica Final   JAVIER MARTINEZ MOLINA

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import socket
import sys
import os


class XMLHandler(ContentHandler):

    def __init__(self):
        self.etiquetas = {'account': ['username', 'passwd'],
            'uaserver': ['ip', 'puerto'],
            'rtpaudio': ['puerto'],
            'regproxy': ['ip', 'puerto'],
            'log': ['path'],
            'audio': ['path']}
  
        self.list_etiquetas = []
        
        self.dic_etiq = {'account_username': '', 'account_passwd': '',
            'uaserver_ip': '', 'uaserver_puerto': '', 'rtpaudio_puerto': '',
            'regproxy_ip': '', 'regproxy_puerto': '', 'log_path': '',
            'audio_path': ''}

    def startElement(self, name, attrs):
        dic = {}
        if name in self.etiquetas:
            dic["name"] = name
            for atributo in self.etiquetas[name]:
                dic[atributo] = attrs.get(atributo, "")
            self.list_etiquetas.append(dic)
        for dic in self.list_etiquetas:
            for etiqueta in dic:
                if dic["name"] == 'account':
                    if etiqueta == "username":
                        self.dic_etiq['account_username'] = dic[etiqueta]
                    if etiqueta == "passwd":
                        self.dic_etiq['account_passwd'] = dic[etiqueta]
                if dic["name"] == 'uaserver':
                    if etiqueta == "ip":
                        self.dic_etiq['uaserver_ip'] = dic[etiqueta]
                    if etiqueta == "puerto":
                        self.dic_etiq['uaserver_puerto'] = dic[etiqueta]
                if dic["name"] == 'rtpaudio':
                    if etiqueta == "puerto":
                        self.dic_etiq['rtpaudio_puerto'] = dic[etiqueta]
                if dic["name"] == 'regproxy':
                    if etiqueta == "ip":
                        self.dic_etiq['regproxy_ip'] = dic[etiqueta]
                    if etiqueta == "puerto":
                        self.dic_etiq['regproxy_puerto'] = dic[etiqueta]
                if dic["name"] == 'log':
                    if etiqueta == "path":
                        self.dic_etiq['log_path'] = dic[etiqueta]
                if dic["name"] == 'audio':
                    if etiqueta == "path":
                        self.dic_etiq['audio_path'] = dic[etiqueta]


if __name__ == "__main__":


    list_metodo = ['INVITE', 'REGISTER', 'BYE']

    #Comprobación de posibles excepciones
    if len(sys.argv) != 4:
        print 'Usage: python uaclient.py config method option'
        raise SystemExit

    if sys.argv[2].upper() not in list_metodo:
        print 'Usage: python uaclient.py config method option'
        raise SystemExit

    METODO = str(sys.argv[2]).upper()
    FICHERO = str(sys.argv[1])
    OPCION = str(sys.argv[3])

    
    parser = make_parser()
    chandler = XMLHandler()
    parser.setContentHandler(chandler)
    parser.parse(open(FICHERO))
    
    USERNAME = chandler.dic_etiq['account_username']
    PASSWD = chandler.dic_etiq['account_passwd']
    UASERVER_IP = chandler.dic_etiq['uaserver_ip']
    UASERVER_PORT = chandler.dic_etiq['uaserver_puerto']
    RTPAUDIO_PORT = chandler.dic_etiq['rtpaudio_puerto']
    REGPROXY_IP = chandler.dic_etiq['regproxy_ip']
    REGPROXY_PORT = chandler.dic_etiq['regproxy_puerto']
    LOG_PATH = chandler.dic_etiq['log_path']
    AUDIO_PATH = chandler.dic_etiq['audio_path']
    
    print chandler.dic_etiq


    if METODO == "REGISTER":
        try:
            int(OPCION)
        except ValueError:
            print 'Usage: python uaclient.py config method option'
            raise SystemExit
            
        LINE = METODO + " sip:" + DIRECCION + " SIP/2.0" + "\r\n\r\n"
        LINE = LINE + "Expires: " + OPCION + "\r\n\r\n"
       

    if METODO == "INVITE" or METODO == "BYE":
        # Contenido que vamos a enviar
        LINE = METODO + " sip:" + LOGIN + "@" + IP_SERVER + " SIP/2.0\r\n\r\n"
        
        
    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((IP_SERVER, PORT))

    try:
        #Envio del mensaje
        my_socket.send(LINE + '\r\n')
        print "Enviando: " + LINE
        #Recibimos el mensaje
        data = my_socket.recv(1024)
    except socket.error:
        print 'Error: No server listening at ' + IP_SERVER + ' port ' + str(PORT)
        raise SystemExit

    print 'Recibido -- \r\n\r\n', data

        
    if METODO == "INVITE":
        if data.split("\r\n\r\n")[0] == "SIP/2.0 100 Trying":
            if data.split("\r\n\r\n")[1] == "SIP/2.0 180 Ringing":
                if data.split("\r\n\r\n")[2] == "SIP/2.0 200 OK":
                    ack = "ACK sip:" + LOGIN + "@" + IP_SERVER + " SIP/2.0\r\n\r\n"
                    my_socket.send(ack + "\r\n")

    print "Terminando socket..."
    my_socket.close()
    print "Fin."

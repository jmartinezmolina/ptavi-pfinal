#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#Práctica 6 - Javier Martínez Molina
"""
Clase (y programa principal) para un servidor SIP en UDP simple
"""
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import SocketServer
import sys
import os
import uaclient

list_metodo = ['INVITE', 'BYE', 'ACK']
P_MP3 = str(23032)
#MP3 = sys.argv[3]


class SipHandler(SocketServer.DatagramRequestHandler):
    """
    Sip server class
    """
    list_palabras = []
    dic_info = {}
    
    def handle(self):

        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            if not line:
                break
            else:
                control = line.find('sip:')
                control2 = line.find('@')
                control3 = line.find('SIP/2.0')
                #Comprobacion de estructura del mensaje recibido
                if control >= 0 and control2 >= 0 and control3 >= 0:
                    metodo = line.split(" ")[0]
                    ip_client = str(self.client_address[0])
                    print line
                    #Comprobacion del metodo del mensaje recibido
                    if metodo == "INVITE":
                        self.list_palabras = line.split("\r\n")
                        print self.list_palabras
                        for linea in self.list_palabras:
                            key_value = linea.split('=')
                            print key_value
                            if len(key_value) == 2:
                                self.dic_info[key_value[0]] = key_value[1]
                        print self.dic_info
                        msg = "SIP/2.0 100 Trying\r\n\r\n"
                        msg += "SIP/2.0 180 Ringing\r\n\r\n"
                        msg += "SIP/2.0 200 OK\r\n\r\n"
                        self.wfile.write(msg)
                    elif metodo == "ACK":
                        print 'recibido ackkkkkkkkkkkkkkkkkkkk'
                        os.system('chmod 755 mp32rtp')
                        run = './mp32rtp -i ' + ip_client + ' -p '
                        #run += RTPAUDIO_PORT + ' < ' + AUDIO_PATH
                        os.system(run)
                    elif metodo == "BYE":
                        self.wfile.write("SIP/2.0 200 OK\r\n\r\n")
                    elif metodo not in list_metodo:
                        excepcion = "SIP/2.0 405 Method Not Allowed\r\n\r\n"
                        self.wfile.write(excepcion)
                else:
                    self.wfile.write('SIP/2.0 400 Bad Request\r\n\r\n')
            break

if __name__ == "__main__":
    # Creamos servidor SIP y escuchamos
    
    #Comprobación de posibles excepciones
    if len(sys.argv) != 2:
        print 'Usage: python uaserver.py config'
        raise SystemExit
    
    FICHERO = str(sys.argv[1])
    
    parser = make_parser()
    chandler = uaclient.XMLHandler()
    parser.setContentHandler(chandler)
    parser.parse(open(FICHERO))
    
    USERNAME = chandler.dic_etiq['account_username']
    PASSWD = chandler.dic_etiq['account_passwd']
    UASERVER_IP = chandler.dic_etiq['uaserver_ip']
    RTPAUDIO_PORT = int(chandler.dic_etiq['rtpaudio_puerto'])
    REGPROXY_IP = chandler.dic_etiq['regproxy_ip']
    REGPROXY_PORT = int(chandler.dic_etiq['regproxy_puerto'])
    LOG_PATH = chandler.dic_etiq['log_path']
    AUDIO_PATH = chandler.dic_etiq['audio_path']

    if not os.path.exists(AUDIO_PATH):
        print 'Usage: python uaserver.py config'
        raise SystemExit

    try:
        UASERVER_PORT = int(chandler.dic_etiq['uaserver_puerto'])
    except ValueError:
        print 'Usage: python uaserver.py config'
        raise SystemExit
    
    serv = SocketServer.UDPServer(("", UASERVER_PORT), SipHandler)
    print "listening...\r\n"
    serv.serve_forever()

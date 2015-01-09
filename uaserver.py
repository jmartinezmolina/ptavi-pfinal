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
import time

list_metodo = ['INVITE', 'BYE', 'ACK']


class SipHandler(SocketServer.DatagramRequestHandler):
    """
    Sip server class
    """
    list_palabras = []
    dic_info = {}

    def add_to_log(self, LOG_PATH, add):

        hora = str(time.strftime("%Y%m%d%H%M%S", time.gmtime()))
        recorte = add.split('\r\n')
        ' '.join(recorte)
        fich = open(LOG_PATH, "a")
        fich.write(hora + ' ' + recorte[0] + '...\r\n')

    def handle(self):

        global USERNAME, UASERVER_IP, RTPAUDIO_PORT, REGPROXY_IP, REGPROXY_PORT

        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            print line
            if not line:
                break
            else:
                control = line.find('sip:')
                control2 = line.find('@')
                control3 = line.find('SIP/2.0')
                #Comprobacion de estructura del mensaje recibido
                if control >= 0 and control2 >= 0 and control3 >= 0:
                    metodo = line.split(" ")[0]
                    #Comprobacion del metodo del mensaje recibido
                    if metodo == "INVITE":

                        self.list_palabras = line.split("\r\n")
                        for linea in self.list_palabras:
                            key_value = linea.split('=')
                            if len(key_value) == 2:
                                self.dic_info[key_value[0]] = key_value[1]
                        msg = "SIP/2.0 100 Trying\r\n\r\n"
                        msg += "SIP/2.0 180 Ringing\r\n\r\n"
                        msg += "SIP/2.0 200 OK\r\n"
                        msg += "Content-Type: application/sdp\r\n\r\n"
                        msg += "v=0\r\n" + "o=" + USERNAME + " " + UASERVER_IP
                        msg += "\r\n" + "s=misesion\r\n" + "t=0\r\n"
                        msg += "m=audio " + str(RTPAUDIO_PORT) + " RTP\r\n\r\n"

                        self.wfile.write(msg)

                        add = " Send to " + str(REGPROXY_IP) + ":"
                        add += str(REGPROXY_PORT) + ' ' + str(msg)
                        self.add_to_log(LOG_PATH, add)

                    elif metodo == "ACK":

                        ip_client = self.dic_info['o'].split(' ')
                        port_rtp = self.dic_info['m'].split(' ')
                        ejecutar_vlc = "cvlc rtp://@" + UASERVER_IP
                        ejecutar_vlc += ":" + str(RTPAUDIO_PORT) + "&"
                        os.system(ejecutar_vlc)
                        os.system('chmod 755 mp32rtp')
                        run = './mp32rtp -i ' + ip_client[1] + ' -p '
                        run += port_rtp[1] + ' < ' + AUDIO_PATH
                        os.system(run)
                        add = " Send to " + ip_client[1] + ":"
                        add += str(port_rtp[1]) + " " + AUDIO_PATH
                        self.add_to_log(LOG_PATH, add)

                    elif metodo == "BYE":
                        msg = "SIP/2.0 200 OK\r\n\r\n"
                        self.wfile.write(msg)
                        add = " Send to " + str(REGPROXY_IP) + ":"
                        add += str(REGPROXY_PORT) + ' ' + str(msg)
                        self.add_to_log(LOG_PATH, add)

                    elif metodo not in list_metodo:
                        excepcion = "SIP/2.0 405 Method Not Allowed\r\n\r\n"
                        self.wfile.write(excepcion)
                        add = " Send to " + str(REGPROXY_IP) + ":"
                        add += str(REGPROXY_PORT) + ' ' + str(excepcion)
                        self.add_to_log(LOG_PATH, add)
                else:
                    excepcion = 'SIP/2.0 400 Bad Request\r\n\r\n'
                    self.wfile.write(excepcion)
                    add = " Send to " + str(REGPROXY_IP) + ":"
                    add += str(REGPROXY_PORT) + ' ' + str(excepcion)
                    self.add_to_log(LOG_PATH, add)
            break

if __name__ == "__main__":

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
    UASERVER_IP = chandler.dic_etiq['uaserver_ip']
    LOG_PATH = chandler.dic_etiq['log_path']
    AUDIO_PATH = chandler.dic_etiq['audio_path']
    REGPROXY_IP = chandler.dic_etiq['regproxy_ip']

    try:
        RTPAUDIO_PORT = int(chandler.dic_etiq['rtpaudio_puerto'])
        REGPROXY_PORT = int(chandler.dic_etiq['regproxy_puerto'])
    except ValueError:
        print "Error: The port must be an integer"
        raise SystemExit

    if UASERVER_IP == "":
        UASERVER_IP = "127.0.0.1"
    else:
        try:
            socket.inet_aton(UASERVER_IP)
            socket.inet_aton(REGPROXY_IP)
        except socket.error:
            print "Error: IP invalid"
            raise SystemExit

    if not os.path.exists(LOG_PATH):
        print 'Usage: python uaserver.py config'
        raise SystemExit

    if not os.path.exists(AUDIO_PATH):
        print 'Usage: python uaserver.py config'
        raise SystemExit

    try:
        UASERVER_PORT = int(chandler.dic_etiq['uaserver_puerto'])
    except ValueError:
        print 'Usage: python uaserver.py config'
        raise SystemExit

    chandler.add_to_log(LOG_PATH, ' listening')
    serv = SocketServer.UDPServer(("", UASERVER_PORT), SipHandler)
    print "listening...\r\n"
    serv.serve_forever()

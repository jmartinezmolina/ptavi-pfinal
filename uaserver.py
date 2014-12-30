#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#Práctica 6 - Javier Martínez Molina
"""
Clase (y programa principal) para un servidor SIP en UDP simple
"""

import SocketServer
import sys
import os

list_metodo = ['INVITE', 'BYE', 'ACK']
P_MP3 = str(23032)
MP3 = sys.argv[3]

#Comprobación de posibles excepciones
if not os.path.exists(MP3):
    print 'Usage: python server.py IP port audio_file'
    raise SystemExit

if len(sys.argv) != 4:
    print 'Usage: python server.py IP port audio_file'
    raise SystemExit

try:
    PORT = int(sys.argv[2])
except ValueError:
    print 'Usage: python server.py IP port audio_file'
    raise SystemExit


class SipHandler(SocketServer.DatagramRequestHandler):
    """
    Sip server class
    """
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
                        msg = "SIP/2.0 100 Trying\r\n\r\n"
                        msg += "SIP/2.0 180 Ringing\r\n\r\n"
                        msg += "SIP/2.0 200 OK\r\n\r\n"
                        self.wfile.write(msg)
                    elif metodo == "ACK":
                        os.system('chmod 755 mp32rtp')
                        prog = './mp32rtp -i '
                        run = prog + ip_client + ' -p ' + P_MP3 + ' < ' + MP3
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
    serv = SocketServer.UDPServer(("", PORT), SipHandler)
    print "listening...\r\n"
    serv.serve_forever()

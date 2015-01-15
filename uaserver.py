#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
# Roger Urrutia Bayo
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""


import SocketServer
import sys
import os
import time
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

diccionario = {}


def escribir_log(mensaje_log, fich_log):
    fecha = time.gmtime(time.time() + int(3600))
    fechaformato = time.strftime("%Y%m%d%H%M%S", fecha)
    log = open(fich_log, 'a')  # 'a' para añadir al final
    log.write(str(fechaformato) + '\t' + mensaje_log + '\r\n')
    log.close()


def saltos_a_blancos(mensaje):
    mensaje = mensaje.split('\r\n')
    mensaje_log = ''
    for linea in mensaje:
        mensaje_log = mensaje_log + ' ' + linea
    return mensaje_log


class XMLHandler(ContentHandler):
    def __init__(self):
        self.username = ""
        self.us_ip = ""
        self.us_puerto = ""
        self.rtpaudio_puerto = ""
        self.regproxy_ip = ""
        self.regproxy_puerto = ""
        self.file_log = ""
        self.file_audio = ""
        self.dicc = {}

    def startElement(self, name, attrs):
        if name == "account":
            self.username = attrs.get('username', "")
            self.dicc['username'] = self.username
        elif name == "uaserver":
            self.us_ip = attrs.get('ip', "127.0.0.1")
            self.us_puerto = attrs.get('puerto', "")
            self.dicc['ip'] = self.us_ip
            self.dicc['puerto'] = self.us_puerto
        elif name == "rtpaudio":
            self.rtpaudio_puerto = attrs.get('puerto', "")
            self.dicc['puertortp'] = self.rtpaudio_puerto
        elif name == "regproxy":
            self.regproxy_ip = attrs.get('ip', "")
            self.regproxy_puerto = attrs.get('puerto', "")
            self.dicc['ip_proxy'] = self.regproxy_ip
            self.dicc['puerto_proxy'] = self.regproxy_puerto
        elif name == "log":
            self.file_log = attrs.get('path', "")
            self.dicc['file_log'] = self.file_log
        elif name == "audio":
            self.file_audio = attrs.get('path', "")
            self.dicc['file_audio'] = self.file_audio
        elif name != "config":
            print 'Alguno de las etiquetas no es correcta'

    def get_tags(self):
        return self.dicc


class SipHandler(SocketServer.DatagramRequestHandler):
    """
    SIP server class
    """
    def handle(self):
        # Recibimos del cliente
        x = True
        while x:
            line = str(self.rfile.read())
            ip = self.client_address
            metodo = line.split(' ')[0]
            mensaje_log = 'Received from ' + ip[0] + ':' + str(ip[1]) + ': ' +\
                          saltos_a_blancos(line) + " [..]"
            escribir_log(mensaje_log, ficheroXML['file_log'])

            print 'Recibo: ' + metodo
            if metodo == 'INVITE':
                #Mando las respuestas al INVITE
                respuesta = "SIP/2.0 100 Trying\r\n\r\n"
                respuesta += "SIP/2.0 180 Ringing\r\n\r\n"
                respuesta += 'SIP/2.0 200 OK\r\n'
                respuesta += 'Content-Type: application/sdp\r\n\r\n'
                respuesta += 'v=0\r\n' + 'o=' + ficheroXML['username']
                respuesta += ' ' + ficheroXML['ip'] + '\r\n'
                respuesta += 's=misesion\r\n' + 't=0\r\n' + 'm=audio '
                respuesta += str(ficheroXML['puertortp']) + ' RTP\r\n\r\n'
                self.wfile.write(respuesta)
                print 'Respondemos al INVITE'
                # sacamos los datos y los guardamos en diccionario
                datos = line.split('\r\n')[4].split(' ')
                diccionario['uc_ip'] = datos[1]
                diccionario['cliente'] = datos[0].split('=')[1]
                diccionario['rtppuerto'] = line.split('\r\n')[7].split(' ')[1]
                mensaje_log = 'Sent to ' + ip[0] + ':' + str(ip[1]) + ': ' + \
                              saltos_a_blancos(respuesta) + " [..]"
                escribir_log(mensaje_log, ficheroXML['file_log'])
            elif metodo == 'ACK':
                #Envio RTP
                print 'Intercambio rtp con usuario: ' + diccionario['cliente']
                aEjecutar = './mp32rtp -i ' + diccionario['uc_ip'] + ' -p ' +\
                            diccionario['rtppuerto'] + ' < ' +\
                            ficheroXML['file_audio']
                os.system("chmod +x mp32rtp")
                os.system(aEjecutar)
                mensaje_log = 'Intercambio de RTP con usuario: ' +\
                              diccionario['cliente'] + ' en el puerto ' +\
                              diccionario['rtppuerto'] + " [..]"
                escribir_log(mensaje_log, ficheroXML['file_log'])
            elif metodo == 'BYE':
                #Mando la confirmacion de haber recibido el BYE
                print 'Enviamos OK del BYE'
                respuesta = "SIP/2.0 200 OK\r\n\r\n"
                self.wfile.write(respuesta)
                mensaje_log = 'Sent to ' + ip[0] + ':' + str(ip[1]) + ': ' + \
                              saltos_a_blancos(respuesta) + " [..]"
                escribir_log(mensaje_log, ficheroXML['file_log'])
            else:
                #Respuestas de error
                print 'Envio error'
                respuesta = "SIP/2.0 400 Bad Request\r\n\r\n"
                respuesta = respuesta + "SIP/2.0 405 Method Not Allowed\r\n\r\n"
                self.wfile.write(respuesta)
                mensaje_log = 'Sent to ' + ip[0] + ':' + str(ip[1]) + ': ' + \
                    saltos_a_blancos(respuesta) + " [..]"
                escribir_log(mensaje_log, ficheroXML['file_log'])
            x = False
            if not line:
                break

if __name__ == "__main__":
    # Comprobamos los datos que entran y los almacenamos
    if len(sys.argv) != 2:
        print 'Usage: python uaclient.py config'
        sys.exit()
    try:
        config = sys.argv[1]
    except IndexError:
        print 'Usage: python uaserver.py config'
        sys.exit()

    # Leemos los datos del DTD mediante la interfaz SAX
    parser = make_parser()
    cHandler = XMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(config))

    # Recuperamos los datos del fichero XML y los almacenamos
    ficheroXML = cHandler.get_tags()
    Puerto = ficheroXML['puerto']
    IP = ficheroXML['ip']

    # Preparamos el socket server
    serv = SocketServer.UDPServer((IP, int(Puerto)), SipHandler)

    print "Empezamos..."
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print 'servidor interrumpido'

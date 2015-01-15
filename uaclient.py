#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
# Roger Urrutia Bayo
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
import uaserver
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

# Comprobamos los datos que entran y los almacenamos
if len(sys.argv) != 4:
    print 'Usage: python uaclient.py config method option'
    sys.exit()
try:
    config = sys.argv[1]
    metodo = sys.argv[2]
    opcion = sys.argv[3]
except IndexError:
    print 'Usage: python cliente.py config method option'
    sys.exit()

# Leemos los datos del DTD mediante la interfaz SAX
parser = make_parser()
cHandler = uaserver.XMLHandler()
parser.setContentHandler(cHandler)
try:
    parser.parse(open(config))
except IOError:
    print 'Usage: python uaclient.py config method option'
    sys.exit()

# Recuperamos los datos del fichero XML y los almacenamos
ficheroXML = cHandler.get_tags()
usuario = ficheroXML['username']  # nombre del usuario
IP_Proxy = ficheroXML['ip_proxy']  # ip del proxy (proxy_registrar.py)
Puerto_Proxy = ficheroXML['puerto_proxy']  # puerto del proxy
puerto_UA = ficheroXML['puerto']  # puerto del user agent
IP_UA = ficheroXML['ip']  # ip del user agent
puertortp = str(ficheroXML['puertortp'])  # puerto rtp para el audio

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((IP_Proxy, int(Puerto_Proxy)))

print "Empezamos..."
mensaje_log = '...'
uaserver.escribir_log(mensaje_log, ficheroXML['file_log'])
mensaje_log = 'Starting...'
uaserver.escribir_log(mensaje_log, ficheroXML['file_log'])

# Preparo el mensaje para enviar
if metodo == 'REGISTER':
    print "Envio Register"
    mensaje = metodo + ' sip:' + usuario + ':' + puerto_UA + ' SIP/2.0\r\n' + \
        'Expires: ' + opcion + '\r\n\r\n'
    mensaje_log = 'Sent to ' + IP_Proxy + ':' + Puerto_Proxy + ': ' + \
                  uaserver.saltos_a_blancos(mensaje) + " [..]"
    uaserver.escribir_log(mensaje_log, ficheroXML['file_log'])
elif metodo == 'INVITE':
    print "Envio INVITE"
    mensaje = metodo + ' sip:' + opcion + ' SIP/2.0\r\n' + \
        'Content-Type: application/sdp\r\n\r\n' + \
        'v=0\r\n' + \
        'o=' + usuario + ' ' + IP_UA + '\r\n' + \
        's=misesion\r\n' + \
        't=0\r\n' + \
        'm=audio ' + puertortp + ' RTP\r\n\r\n'
    mensaje_log = 'Sent to ' + IP_Proxy + ':' + Puerto_Proxy + ': ' + \
                  uaserver.saltos_a_blancos(mensaje) + " [..]"
    uaserver.escribir_log(mensaje_log, ficheroXML['file_log'])
elif metodo == 'BYE':
    print "Envio BYE"
    mensaje = metodo + ' sip:' + opcion + ' SIP/2.0\r\n\r\n'
    mensaje_log = 'Sent to ' + IP_Proxy + ':' + Puerto_Proxy + ': ' + \
                  uaserver.saltos_a_blancos(mensaje) + " [..]"
    uaserver.escribir_log(mensaje_log, ficheroXML['file_log'])
else:
    print 'Usage: python uaclient.py config method option'
    sys.exit()

# envio el mensaje
my_socket.send(mensaje)

# Analizamos las respuestas del server
try:
    data = my_socket.recv(1024)
except socket.error:
    print 'Error: no server listening at ' + IP_Proxy + ' port ' + Puerto_Proxy
    mensaje_log = 'Error: no server listening at ' + \
                  IP_Proxy + ' port ' + Puerto_Proxy + " [..]"
    uaserver.escribir_log(mensaje_log, ficheroXML['file_log'])
    sys.exit()

print 'Recibido: ' + uaserver.saltos_a_blancos(data)

#Segun lo que recibo lo trato
respuesta = data.split("SIP/2.0 ")[1]
if respuesta == '100 Trying\r\n':
    mensaje_log = 'Received from ' + IP_Proxy + ':' + Puerto_Proxy + ': ' + \
                  uaserver.saltos_a_blancos(data) + " [..]"
    uaserver.escribir_log(mensaje_log, ficheroXML['file_log'])

    #Mandamos ACK al servidor
    print "Mandamos ack"
    iprtp = data.split('\r\n')[6].split(' ')[1]
    puertortp = data.split('\r\n')[9].split(' ')[1]
    mensaje = 'ACK sip:' + opcion + ' SIP/2.0' + '\r\n\r\n'
    my_socket.send(mensaje)
    mensaje_log = 'Sent to ' + IP_Proxy + ':' + Puerto_Proxy + ': ' + \
                  uaserver.saltos_a_blancos(mensaje) + " [..]"
    uaserver.escribir_log(mensaje_log, ficheroXML['file_log'])

    #Ejecutamos el intercambio de la rtp
    print "Intercambio de rtp con usuario: " + opcion
    aEjecutar = './mp32rtp -i ' + iprtp + ' -p ' + \
        puertortp + ' < ' + ficheroXML['file_audio']
    os.system("chmod +x mp32rtp")
    os.system(aEjecutar)
    mensaje_log = 'Intercambio de rtp con usuario: ' + opcion + " [..]"
    uaserver.escribir_log(mensaje_log, ficheroXML['file_log'])
elif respuesta == '200 OK\r\n':
    print "Recibimos 200 ok"
    mensaje_log = 'Received from ' + IP_Proxy + ':' + Puerto_Proxy + ': ' + \
                  uaserver.saltos_a_blancos(data) + " [..]"
    uaserver.escribir_log(mensaje_log, ficheroXML['file_log'])
elif respuesta == '400 Bad Request\r\n':
    #Imprimimos el error
    print 'Error: ' + uaserver.saltos_a_blancos(respuesta)
else:
    #Recibido mensaje Error
    print 'Error: Respuesta incorrecta'
    mensaje_log = 'Error: ' + uaserver.saltos_a_blancos(data) + " [..]"
    uaserver.escribir_log(mensaje_log, ficheroXML['file_log'])

# Cerramos todo
my_socket.close()
print "Fin."
mensaje_log = 'Finishing.'
uaserver.escribir_log(mensaje_log, ficheroXML['file_log'])

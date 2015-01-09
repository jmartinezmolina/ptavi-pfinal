#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
# Roger Urrutia Bayo
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import SocketServer
import sys
import os
import socket
import time
import uaserver
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class XMLHandler(ContentHandler):
    def __init__(self):
        self.name = ''
        self.us_ip = ''
        self.us_puerto = ''
        self.database = ''
        self.log = ''
        self.dicc = {}

    def startElement(self, name, attrs):
        if name == "server":
            self.name = attrs.get('name', "")
            self.dicc['name'] = self.name
            self.us_ip = attrs.get('ip', "")
            self.us_puerto = attrs.get('puerto', "127.0.0.1")
            self.dicc['ip'] = self.us_ip
            self.dicc['puerto'] = self.us_puerto
        elif name == "database":
            self.database = attrs.get('path', "")
            self.dicc['database'] = str(self.database)
        elif name == "log":
            self.log = attrs.get('path', "")
            self.dicc['log'] = self.log
        elif name != "config":
            print 'Alguno de las etiquetas no es correcta'

    def get_tags(self):
        return self.dicc


# devuelve la informacion del cliente si este aun esta registrado
def buscar_cliente(cliente):
    fecha = time.gmtime(time.time() + int(3600))
    fechaformato = time.strftime("%Y%m%d%H%M%S", fecha)
    database = open(ficheroXML['database'])
    datos = database.readlines()
    lista_vacia = True
    if len(datos) > 0:
        for linea in datos:
            usuario = linea.split('\t')
            expires = float(fechaformato) - float(usuario[0])
            if usuario[1] == cliente and expires < float(usuario[4]):
                lista = usuario
                lista_vacia = False
    if lista_vacia:
        lista = []
    database.close()
    return lista


def insertar_usuario(usuario, ip, puerto, expires):
    fecha = time.gmtime(time.time() + int(3600))
    fechaformato = time.strftime("%Y%m%d%H%M%S", fecha)
    database = open(ficheroXML['database'])
    datos = database.readlines()
    database.close()
    inserto = True
    dicc = {}

    if len(datos) > 0:  # si la database tiene datos
        # almaceno los datos del txt en dicc y compruebo si estan registrados
        for linea in datos:
            user = linea.split('\t')
            dicc[user[1]] = user[0], user[1], user[2],\
                user[3], user[4].split('\r\n')[0]
            if float(fechaformato) - float(user[0]) >= float(user[4]):
                del dicc[user[1]]
        database = open(ficheroXML['database'], 'w')
        for registrado in dicc.keys():
            # si el usuario no esta en el documento lo dejo como estaba
            if usuario != registrado:
                datos_user = dicc[registrado]
                mensaje_log = datos_user[1] + '	' + \
                    datos_user[2] + '	' + datos_user[3] + '	' + \
                    datos_user[4]
                uaserver.escribir_log(mensaje_log, ficheroXML['database'])
            else:
                # si el expires que le paso es <= 0 es para borrarlo
                if int(expires) <= 0:
                    del dicc[registrado]
                # si el expires es mayor lo registro como nuevo
                else:
                    # si quiero poder actualizar el expires es aqui... !!!!
                    datos_user = dicc[registrado]
                    mensaje_log = datos_user[1] + '	' + \
                        datos_user[2] + '	' + datos_user[3] + '	' + \
                        expires
                    uaserver.escribir_log(mensaje_log, ficheroXML['database'])
                    inserto = False
        # si el usuario no estaba en el documento y el expires es > 0 lo añado
        if inserto and int(expires) > 0:
            mensaje_log = usuario + '	' + ip + '	' + \
                str(puerto) + '	' + expires
            uaserver.escribir_log(mensaje_log, ficheroXML['database'])
        database.close()
    else:  # si la database esta vacia, añado el usuario
        database = open(ficheroXML['database'], 'w')  # 'w' escribe al principi
        mensaje_log = usuario + '	' + ip + '	' + \
            str(puerto) + '	' + str(expires)
        uaserver.escribir_log(mensaje_log, ficheroXML['database'])
        database.close()


def preparo_respuesta(metodo, line, ip):
    usuario = line.split('\r\n')[0].split(' ')[1].split(':')[1]
    if metodo == 'REGISTER':  # Guardo el usuario en la database
        expires = line.split('\r\n')[1].split(' ')[1]
        puerto_UA = line.split('\r\n')[0].split(' ')[1].split(':')[2]

        insertar_usuario(usuario, ip, puerto_UA, expires)
        respuesta = 'SIP/2.0 200 OK\r\n'
    else:
        lista = buscar_cliente(usuario)  # linea de ese usuario
        if len(lista) > 0:  # si esta en la lista...
            ip_UA = lista[2]
            puerto_UA = lista[3]
            # reenvio el mensaje
            my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect((ip_UA, int(puerto_UA)))
            my_socket.send(line)
            if metodo == 'INVITE':
                print "Envio el invite al UA " + puerto_UA

                mensaje_log = 'Sent to ' + ip_UA + ':' + puerto_UA + ': ' + \
                              uaserver.saltos_a_blancos(line) + "[..]"
                uaserver.escribir_log(mensaje_log, ficheroXML['log'])
                try:
                    # si recibo respuesta...
                    respuesta = my_socket.recv(1024)
                    mensaje_log = 'Received from ' + ip_UA + ':' + puerto_UA +\
                                  ': ' + uaserver.saltos_a_blancos(respuesta)\
                                  + "[..]"
                    uaserver.escribir_log(mensaje_log, ficheroXML['log'])
                    print "recibo respuesta del invite"
                except socket.error:
                    # si no recibo respuesta...
                    respuesta = 'SIP/2.0 400 Bad Request' + '\r\n'
                    print "no recibo respuesta del invite"
            elif metodo == 'ACK':
                print "Envio el ACK al UA " + puerto_UA
                mensaje_log = 'Sent to ' + ip_UA + ':' + puerto_UA + ': ' + \
                              uaserver.saltos_a_blancos(line) + "[..]"
                uaserver.escribir_log(mensaje_log, ficheroXML['log'])
                respuesta = ''
            elif metodo == 'BYE':
                print "Envio el BYE al UA " + puerto_UA
                mensaje_log = 'Sent to ' + ip_UA + ':' + puerto_UA + ': ' + \
                              uaserver.saltos_a_blancos(line) + "[..]"
                uaserver.escribir_log(mensaje_log, ficheroXML['log'])
                try:
                    respuesta = my_socket.recv(1024)
                    mensaje_log = 'Received from ' + ip_UA + ':' + puerto_UA +\
                                  ': ' + uaserver.saltos_a_blancos(respuesta)
                    uaserver.escribir_log(mensaje_log, ficheroXML['log'])
                    print "recibo respuesta del BYE"
                except socket.error:
                    respuesta = 'SIP/2.0 400 Bad Request' + '\r\n'
                    print "no recibo respuesta del BYE"
            else:
                respuesta = 'SIP/2.0 405 Method Not Allowed'
        else:  # si no esta en la database no realiza nada
            insertar_usuario(usuario, ip, '', 0)
            respuesta = 'SIP/2.0 404 User Not Found' + '\r\n'
            print "el usuario no esta en la database"

    return respuesta


class EchoHandler(SocketServer.DatagramRequestHandler):
    """
    Echo server class
    """
    def handle(self):
        # Recibe del cliente y comprueba que metodo para tratarlo
        # segun convenga
        x = True
        while x:
            line = str(self.rfile.read())
            metodo = line.split(' ')[0]
            ip = self.client_address[0]
            puerto = self.client_address[1]
            mensaje_log = 'Received from ' + ip + ':' + str(puerto) + ': ' + \
                          uaserver.saltos_a_blancos(line) + " [..]"
            uaserver.escribir_log(mensaje_log, ficheroXML['log'])

            print 'Recibo: ' + metodo

            # Preparo el mensaje, envio una respuesta y almaceno el log
            mensaje = preparo_respuesta(metodo, line, ip)
            if mensaje != '':
                self.wfile.write(mensaje)
                tipo_mensaje = mensaje.split(' ')[1].split(' ')[0]
                if tipo_mensaje != '400':
                    mensaje_log = 'Sent to ' + ip + ':' + str(puerto) + ': ' +\
                                  uaserver.saltos_a_blancos(mensaje) + " [..]"
                    uaserver.escribir_log(mensaje_log, ficheroXML['log'])
                elif tipo_mensaje == '400':
                    mensaje_log = 'Error: ' +\
                                  uaserver.saltos_a_blancos(mensaje) + " [..]"
                    uaserver.escribir_log(mensaje_log, ficheroXML['log'])
            x = False
            if not line:
                break

if __name__ == "__main__":
    # Comprobamos los datos que entran y los almacenamos
    if len(sys.argv) != 2:
        print 'Usage: python uaserver.py config'
        sys.exit()
    try:
        config = str(sys.argv[1])
    except IndexError:
        print 'Usage: python uaserver.py config'
        sys.exit()

    # Leemos los datos del DTD mediante la interfaz SAX
    parser = make_parser()
    cHandler = XMLHandler()
    parser.setContentHandler(cHandler)
    try:
        parser.parse(open(config))
    except IOError:
        print 'Usage: python uaclient.py config method option'
        sys.exit()

    # Recuperamos los datos del fichero XML y los almacenamos
    ficheroXML = cHandler.get_tags()
    Puerto = ficheroXML['puerto']
    IP = ficheroXML['ip']

    # Preparamos el socket server
    serv = SocketServer.UDPServer((IP, int(Puerto)), EchoHandler)

    print "Empezamos..."
    mensaje_log = '...'
    uaserver.escribir_log(mensaje_log, ficheroXML['log'])
    mensaje_log = "Starting..."
    uaserver.escribir_log(mensaje_log, ficheroXML['log'])
    # creamos el fichero primero para poder leerlo
    mensaje_log = ""
    log = open(ficheroXML['database'], 'a')  # 'a' para añadir al final
    log.write(mensaje_log)
    log.close()
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print 'Finishing.'
        mensaje_log = 'Finishing.'
        uaserver.escribir_log(mensaje_log, ficheroXML['log'])

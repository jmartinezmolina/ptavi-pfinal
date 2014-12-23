#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa de Proxy-Registrar
"""
import SocketServer
import sys
import time
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

"""
LEER EL FICHERO XML
"""
class XMLHandler(ContentHandler):

    def __init__(self):
        self.diccionario = {}
        self.atributos = {
            'server': ['name', 'ip', 'puerto'],
            'database': ['path'],
            'log': ['path']
        }

    def startElement(self, tag, attrs):
        if tag in self.atributos:
            for atributo in self.atributos[tag]:
                elemento = tag + "_" + atributo
                self.diccionario[elemento] = attrs.get(atributo, "")

    def get_tags(self):
        return self.diccionario

"""
CLASE ECHO HANDLER
"""
class EchoHandler(SocketServer.DatagramRequestHandler):
    """
    Echo server class
    """
    def handle(self):
        ip_port = self.client_address
        while 1:
            # Leyendo línea a línea lo que nos llega
            line = self.rfile.read()
            if not line:
                break
            print "Recibimos: " + line
            lista = line.split()

            metodo = lista[0]
            metodos_SIP = ("REGISTER", "INVITE", "BYE", "ACK")










if __name__ == "__main__":
    """
    ERRORES EN LA LÍNEA DE COMANDOS
    """
    # Número de elementos introducidos
    if len(sys.argv) != 2:
        print "Usage: python proxy_registrar.py config"
        raise SystemExit

    #Error en el valor CONFIG
    CONFIG = sys.argv[1]

    try:
        CONFIG.split(".")[1]
    except IndexError:
        print "Usage: python proxy_registrar.py config"
        raise SystemExit

    if not CONFIG.split(".")[1] == "xml":
        print "Usage: python proxy_registrar.py config"
        raise SystemExit


    """
    PARSER CON LOS VALORES DE XML
    """
    parser = make_parser()
    sHandler = XMLHandler()
    parser.setContentHandler(sHandler)
    parser.parse(open(CONFIG))
    xml = sHandler.get_tags()


    """
    SOCKET
    """
    # Creamos servidor de eco y escuchamos
            # ---> q puerto ponemos?
    serv = SocketServer.UDPServer(("", int(xml["server_puerto"])), EchoHandler)
    print "\nServer " + xml["server_name"] + " listening at port " + xml["server_puerto"] + "...\r\n"
    serv.serve_forever()

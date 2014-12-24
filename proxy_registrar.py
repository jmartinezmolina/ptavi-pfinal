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
diccionario = {}
formato_time = '%Y-%m-%d %H:%M:%S'

class EchoHandler(SocketServer.DatagramRequestHandler):
    """
    Echo server class
    """
    def handle(self):
        ip = self.client_address[0]
        while 1:
            # Leyendo línea a línea lo que nos llega
            line = self.rfile.read()
            if not line:
                break
            print "Recibimos: " + line
            lista = line.split()

            metodo = lista[0]
            metodos_SIP = ("REGISTER", "INVITE", "BYE", "ACK")

            # Si el método es REGISTER
            if metodo == "REGISTER":
                # Primero vemos si alguien ha expirado
                self.ver_si_expire()
                # Cliente nuevo según su expire
                user = lista[1].split(":")[1]
                puerto = int(lista[1].split(":")[2])
                expires = int(lista[4])
                if expires > 0:
                    if not user in diccionario:
                        print "... entra en el dicc: " + str(user) + "\r"
                    else:
                        print "... modifico del dicc: " + str(user) + "\r"
                    time_exp = time.gmtime(time.time() + expires)
                    day_time_exp = time.strftime(formato_time, time_exp)
                    diccionario[user] = [ip, puerto, day_time_exp]
                    print "diccionario: " + str(diccionario) + "\r"
                else:
                    if user in diccionario:
                        del diccionario[user]
                        print "... borro del dicc a: " + str(user) + "\r"
                        if diccionario:
                            print "diccionario: " + str(diccionario) + "\r"
                self.register2file()
                respuesta = "SIP/2.0 200 OK \r\n\r\n"

            else:
                respuesta = "SIP/2.0 400 Bad Request \r\n\r\n"

            print "\r\n\r\nRespondo al cliente: " + respuesta
            self.wfile.write(respuesta)

    """
    Fichero registered.txt class
    """
    def register2file(self):
        fich = open("registered.txt", 'w')
        fich.write("Username\tIP\tPuerto\tExpires\r\n")
        for user in diccionario.keys():
            ip = str(diccionario[user][0])
            puerto = str(diccionario[user][1])
            expires = str(diccionario[user][2])
            fich.write(user + "\t" + ip + "\t" + puerto + "\t" + expires + "\r\n")
        fich.close()

    """
    Ver si alguien del diccionario ha expirado
    """
    def ver_si_expire(self):
        for user in diccionario.keys():
            expires = str(diccionario[user][2])
            time_now = time.gmtime(time.time())
            day_time_now = time.strftime(formato_time, time_now)
            if expires <= day_time_now:
                del diccionario[user]
                print "... expira del dicc: " + str(user) + "\r"
                if diccionario:
                    print "diccionario: " + str(diccionario) + "\r"



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

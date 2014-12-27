#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa de Proxy-Registrar
"""
import SocketServer
import socket
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
        while 1:
            # Leyendo línea a línea lo que nos llega
            line = self.rfile.read()
            if not line:
                break
            print "Recibimos: " + line
            lista = line.split()
            ip = self.client_address[0]
                        # ---> El proxy debe ver si está bien el método y petición o reenvía lo que llegue?
            # Ver si el método llegado es correcto
            metodo = lista[0]
            metodos_SIP = ("REGISTER", "INVITE", "BYE", "ACK")

            if not metodo in metodos_SIP:
                self.wfile.write('SIP/2.0 405 Method Not Allowed\r\n\r\n')
                print 'Respondo: SIP/2.0 405 Method Not Allowed\r\n\r\n'
            
            else:
                # Si el método es REGISTER
                if metodo == "REGISTER":

                    # Ver si la petición está bien formada
                    protocolo = lista[1].split(':')[0]
                    user = lista[1].split(':')[1]
                    try:
                         #---> ese puerto o del que le llega? self.client_address[1] 
                        puerto = int(lista[1].split(":")[2])
                        expires = int(lista[4])
                    except ValueError:
                        self.wfile.write('SIP/2.0 400 Bad Request\r\n\r\n')
                        print 'Responde: SIP/2.0 400 Bad Request\r\n\r\n'
                    sip_v = lista[2]
                    if protocolo == "sip" and "@" in user and sip_v == "SIP/2.0":

                        # Primero vemos si alguien ha expirado
                        self.ver_si_expire()
                        # Cliente nuevo según su expire
                        if expires > 0:
                            if not user in diccionario:
                                print "... entra en el dicc: " + str(user) + "\r"
                            else:
                                print "... modifico del dicc: " + str(user) + "\r"
                            time_now = time.gmtime(time.time())
                            day_time_now = time.strftime(formato_time, time_now)
                            time_exp = time.gmtime(time.time() + expires)
                            day_time_exp = time.strftime(formato_time, time_exp)
                            diccionario[user] = [ip, puerto, day_time_now, day_time_exp]
                            print "diccionario: " + str(diccionario) + "\r"
                        else:
                            if user in diccionario:
                                del diccionario[user]
                                print "... borro del dicc a: " + str(user) + "\r"
                                if diccionario:
                                    print "diccionario: " + str(diccionario) + "\r"
                        self.register2file()
                        print "Respondo: SIP/2.0 200 OK\r\n\r\n"
                        self.wfile.write("SIP/2.0 200 OK\r\n\r\n")
                    
                    # Si la petición no está bien formada
                    else: 
                        self.wfile.write('SIP/2.0 400 Bad Request\r\n\r\n')
                        print 'Responde: SIP/2.0 400 Bad Request\r\n\r\n'

                # Si el método es INVITE, ACK o BYE
                elif metodo == "INVITE" or "ACK" or "BYE":

                    # Ver si la petición está bien formada
                    protocolo = lista[1].split(':')[0]
                    name = lista[1].split(':')[1]
                    sip_v = lista[2]
                    if protocolo == "sip" and "@" in name and sip_v == "SIP/2.0":
                        
                                        # ---> ver eso tanto en invite como en ack y bye?
                        # Primero vemos si alguien ha expirado
                        self.ver_si_expire()
                        # Vemos si está registrado al que se quiere reenviar
                        registrado = 0
                        registrado = self.ver_si_registered(name, registrado)

                        # Si está registrado y no ha expirado lo reenvío
                        if registrado == 1:
                            my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            my_socket.connect((diccionario[name][0], diccionario[name][1]))
                            print "\nReenviando: " + line
                            my_socket.send(line + '\r\n')
                    
                            # Si el método es INVITE o BYE además espero recibir
                            if metodo == "INVITE" or "BYE":
                                # Error si el servidor no está lanzado
                                try:
                                    data = my_socket.recv(1024)
                                except socket.error:
                                    error = "Error: No server listening at "
                                    error += diccionario[name][0] + " port "
                                    error += str(diccionario[name][1]) + "\r\n"
                                    print error
                                    raise SystemExit
                                # Recibo respuesta y la envío al que solicitó el invite o bye
                                print 'Recibido -- ', data
                                self.wfile.write(data)
                                print "Responde: " + data

                        # Si no está registrado o sí lo estaba pero ha expirado
                        else:
                            print "Responde: SIP/2.0 404 User Not Found\r\n\r\n"
                            self.wfile.write('SIP/2.0 404 User Not Found\r\n\r\n')

                    # Si la petición no está bien formada
                    else: 
                        self.wfile.write('SIP/2.0 400 Bad Request\r\n\r\n')
                        print 'Responde: SIP/2.0 400 Bad Request\r\n\r\n'


    """
    Fichero registered.txt class
    """
    def register2file(self):
        fich = open("registered.txt", 'w')
        fich.write("Username\tIP\tPuerto\tRegistro\tExpires\r\n")
        for user in diccionario.keys():
            ip = str(diccionario[user][0])
            puerto = str(diccionario[user][1])
            registro = str(diccionario[user][2])
            expires = str(diccionario[user][3])
            fich.write(user + "\t" + ip + "\t" + puerto + "\t" + registro + "\t" + expires + "\r\n")
        fich.close()

    """
    Ver si alguien del diccionario ha expirado
    """
    def ver_si_expire(self):
        for user in diccionario.keys():
            expires = str(diccionario[user][3])
            time_now1 = time.gmtime(time.time())
            day_time_now1 = time.strftime(formato_time, time_now1)
            if expires <= day_time_now1:
                del diccionario[user]
                print "... expira del dicc: " + str(user) + "\r"
                if diccionario:
                    print "diccionario: " + str(diccionario) + "\r"

    """
    Ver si está en el fichero registered.txt
    """
    def ver_si_registered(self, name, registrado):
        for user in diccionario.keys():
            if name == user:
                registrado = 1 
        return registrado     


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
    try:
        parser.parse(open(CONFIG))
    except IOError:
        print "Usage: python proxy_registrar.py config"
        raise SystemExit
    xml = sHandler.get_tags()


    """
    SOCKET
    """
    # Creamos servidor de eco y escuchamos
            # ---> q puerto ponemos?
    serv = SocketServer.UDPServer((xml["server_ip"], int(xml["server_puerto"])), EchoHandler)
    print "\nServer " + xml["server_name"] + " listening at port " + xml["server_puerto"] + "...\r\n"
    serv.serve_forever()
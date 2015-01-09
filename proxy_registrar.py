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
        self.dicc = {}
        self.atributos = {
            'server': ['name', 'ip', 'puerto'],
            'database': ['path'],
            'log': ['path']
        }

    def startElement(self, tag, attrs):
        if tag in self.atributos:
            for atributo in self.atributos[tag]:
                elemento = tag + "_" + atributo
                self.dicc[elemento] = attrs.get(atributo, "")

    def get_tags(self):
        return self.dicc

"""
CLASE ECHO HANDLER
"""
dicc = {}
formato = '%Y-%m-%d %H:%M:%S'
form_log = time.strftime('%Y%m%d%H%M%S')


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
            rec_ip = self.client_address[0]
            rec_puerto = self.client_address[1]
            self.log_rec(rec_ip, rec_puerto, line)

            # Ver si el método llegado es correcto
            metodo = line.split()[0]
            metodos_SIP = ("REGISTER", "INVITE", "BYE", "ACK")

            if metodo not in metodos_SIP:
                line_send = 'SIP/2.0 405 Method Not Allowed\r\n'
                self.log_send(rec_ip, rec_puerto, line_send)
                self.wfile.write(line_send + "\r\n")

            else:
                # Si el método es REGISTER
                if metodo == "REGISTER":

                    # Ver si la petición está bien formada
                    protoc = line.split()[1].split(':')[0]
                    user = line.split()[1].split(':')[1]
                    try:
                        puerto = int(line.split()[1].split(":")[2])
                        expires = int(line.split()[4])
                    except ValueError:
                        line_send = 'SIP/2.0 400 Bad Request\r\n'
                        self.log_send(rec_ip, rec_puerto, line_send)
                        self.wfile.write(line_send + "\r\n")
                    sip_v = line.split()[2]

                    if protoc == "sip" and "@" in user and sip_v == "SIP/2.0":

                        # Primero vemos si alguien ha expirado
                        self.ver_si_expire()

                        # Cliente nuevo según su expire
                        if expires > 0:
                            if user not in dicc:
                                print "... entra: " + str(user) + "\r"
                            else:
                                print "... modifico: " + str(user) + "\r"
                            time_now = time.gmtime(time.time())
                            day_t_now = time.strftime(formato, time_now)
                            time_exp = time.gmtime(time.time() + expires)
                            day_t_exp = time.strftime(formato, time_exp)
                            dicc[user] = [rec_ip, puerto, day_t_now, day_t_exp]
                            print "diccionario: " + str(dicc) + "\r"

                        else:
                            if user in dicc:
                                del dicc[user]
                                print "... borro: " + str(user) + "\r"
                                if dicc:
                                    print "diccionario: " + str(dicc) + "\r"

                        self.register2file()
                        line_send = 'SIP/2.0 200 OK\r\n'
                        self.log_send(rec_ip, rec_puerto, line_send)
                        self.wfile.write(line_send + "\r\n")

                    # Si la petición no está bien formada
                    else:
                        line_send = 'SIP/2.0 400 Bad Request\r\n'
                        self.log_send(rec_ip, rec_puerto, line_send)
                        self.wfile.write(line_send + "\r\n")

                # Si el método es INVITE, ACK o BYE
                elif metodo == "INVITE" or "ACK" or "BYE":

                    # Ver si la petición está bien formada
                    protoc = line.split()[1].split(':')[0]
                    name = line.split()[1].split(':')[1]
                    sip_v = line.split()[2]

                    if protoc == "sip" and "@" in name and sip_v == "SIP/2.0":

                        # Primero vemos si alguien ha expirado
                        self.ver_si_expire()
                        # Vemos si está registrado al que se quiere reenviar
                        registrado = 0
                        registrado = self.ver_si_registered(name, registrado)

                        # Si está registrado y no ha expirado lo reenvío
                        if registrado == 1:
                            ip_send = dicc[name][0]
                            p_send = int(dicc[name][1])
                                            # ----> pep8 mal
                            my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            my_socket.connect((ip_send, p_send))
                            self.log_send(ip_send, p_send, line)
                            my_socket.send(line + '\r\n')

                            # Si es INVITE o BYE espero recibir
                            if not metodo == "ACK":
                                # Error si el servidor no está lanzado
                                try:
                                    # Recibo respuesta
                                    data = my_socket.recv(1024)
                                    self.log_rec(ip_send, p_send, data)
                                    # La reenvío al que solicitó el invite o bye
                                    self.log_send(rec_ip, rec_puerto, data)
                                    self.wfile.write(data + "\r\n")
                                except socket.error:
                                    line_log = "Error: No server listening at "
                                    line_log += dicc[name][0] + " port "
                                    line_log += str(p_send) + "\r\n"
                                    print line_log
                                    # log
                                    log = open(xml["log_path"], 'a')
                                    log.write(form_log + ' ' + line_log)
                                    log.close()
                                    # Le envío un 400 Bad Request al que envía el invite o bye
                                    line_send = 'SIP/2.0 400 Bad Request\r\n'
                                    self.log_send(rec_ip, rec_puerto, line_send)
                                    self.wfile.write(line_send + "\r\n")
                                    break

                        # Si no está registrado o sí lo estaba pero ha expirado
                        else:
                            line_send = 'SIP/2.0 404 User Not Found\r\n'
                            self.log_send(rec_ip, rec_puerto, line_send)
                            self.wfile.write(line_send + "\r\n")

                    # Si la petición no está bien formada
                    else:
                        line_send = 'SIP/2.0 400 Bad Request\r\n'
                        self.log_send(rec_ip, rec_puerto, line_send)
                        self.wfile.write(line_send + "\r\n")

    """
    Fichero registered.txt class
    """
    def register2file(self):
        fich = open("registered.txt", 'w')
        fich.write("Username\tIP\tPuerto\tRegistro\tExpires\r\n")
        for user in dicc.keys():
            ip = str(dicc[user][0])
            puerto = str(dicc[user][1])
            registro = str(dicc[user][2])
            expires = str(dicc[user][3])
            write = user + "\t" + ip + "\t" + puerto
            write += "\t" + registro + "\t" + expires
            fich.write(write + "\r\n")
        fich.close()

    """
    Ver si alguien del diccionario ha expirado
    """
    def ver_si_expire(self):
        for user in dicc.keys():
            expires = str(dicc[user][3])
            time_now1 = time.gmtime(time.time())
            day_t_now1 = time.strftime('%Y-%m-%d %H:%M:%S', time_now1)
            if expires <= day_t_now1:
                del dicc[user]
                print "... expira: " + str(user) + "\r"
                if dicc:
                    print "diccionario: " + str(dicc) + "\r"

    """
    Ver si está en el fichero registered.txt
    """
    def ver_si_registered(self, name, registrado):
        for user in dicc.keys():
            if name == user:
                registrado = 1
                print str(name) + " sí está registrado...\r"
        return registrado

    """
    Guardar mensajes de depuración de envío en .log
    """
    def log_send(self, ip, puerto, line_send):
        log = open(xml["log_path"], 'a')
        send_to = "Sent to " + ip + ":" + str(puerto)
        print "\n" + send_to
        line_log = send_to + ": " + line_send.replace('\r\n', ' ') + '\r\n'
        log.write(form_log + ' ' + line_log)
        print '\nEnviando: ' + line_send

    """
    Guardar mensajes de depuración de recibo en .log
    """
    def log_rec(self, ip, puerto, line_rec):
        log = open(xml["log_path"], 'a')
        rec_from = 'Received from ' + ip + ":" + str(puerto)
        print "\n" + rec_from
        line_log = rec_from + ": " + line_rec.replace('\r\n', ' ') + '\r\n'
        log.write(form_log + ' ' + line_log)
        print "\nRecibido -- " + line_rec


if __name__ == "__main__":
    """
    ERRORES EN LA LÍNEA DE COMANDOS
    """
    # Número de elementos introducidos
    if len(sys.argv) != 2:
        print "Usage: python proxy_registrar.py config"
        raise SystemExit

    # Error en el valor CONFIG
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
    server_n = xml["server_name"]
    server_ip = xml["server_ip"]
    if server_ip == "":
        server_ip = "127.0.0.1"
    server_p = int(xml["server_puerto"])
    
    try:
        inicio = "Server " + server_n + " listening at port " + str(server_p) + "...\r\n"
        print "\n" + inicio
        # log
        log = open(xml["log_path"], 'a')
        log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + 'Starting...\r\n')
        log.close()
        # Creamos servidor de eco y escuchamos
        serv = SocketServer.UDPServer((server_ip, server_p), EchoHandler)
        serv.serve_forever()
    except(KeyboardInterrupt):
        # log
        log = open(xml["log_path"], 'a')
        log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + '...Finishing.\r\n\r\n')
        log.close()
        print "\nTerminando proxy..."
        print "\nFin.\r\n"

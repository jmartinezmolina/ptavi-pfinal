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
from uaclient import Log


class XMLHandler(ContentHandler):
    """
    LEER EL FICHERO XML
    """
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


class Registered():
    """
    Leer el fichero registered.txt al iniciar
    """
    def leer_registered(self):
        print "Leyendo base de datos de usuarios registrados...\r"
        try:
            fichero = open("registered.txt", "r")
            db = fichero.readlines()
            fichero.close()
            if len(db) > 1:
                for linea in range(len(db)):
                    user = str(db[linea].split("\t")[0])
                    if not user == "Username":
                        try:
                            ip = str(db[linea].split("\t")[1])
                            puerto = str(db[linea].split("\t")[2])
                            registro = str(db[linea].split("\t")[3])
                            exp = str(db[linea].split("\t")[4])
                            expires = exp.split("\r\n")[0]
                            time_now2 = time.gmtime(time.time())
                            day_t_now2 = time.strftime(formato, time_now2)
                            # Mira si ha expirado alguno
                            if expires > day_t_now2:
                                dicc[user] = [ip, puerto, registro, expires]
                        except IndexError:
                            if dicc == {}:
                                print "... base de datos vacía.\r\n"
                            break
                if dicc:
                    print "diccionario: " + str(dicc) + "\r"
                else:
                    print "... base de datos vacía.\r\n"
            else:
                print "... base de datos vacía.\r\n"
        except IOError:
            print "... base de datos vacía.\r\n"


class SipHandler(SocketServer.DatagramRequestHandler):
    """
    CLASE SIP HANDLER
    """
    def handle(self):
        while 1:
            # Leyendo línea a línea lo que nos llega
            line = self.rfile.read()
            if not line:
                break
            rec_ip = self.client_address[0]
            rec_p = self.client_address[1]
            Log.log_rec(rec_ip, rec_p, line, f_log)

            # Ver si el método llegado es correcto
            metodo = line.split()[0]
            metodos_SIP = ("REGISTER", "INVITE", "BYE", "ACK")

            if metodo not in metodos_SIP:
                line_send = 'SIP/2.0 405 Method Not Allowed\r\n'
                Log.log_send(rec_ip, rec_p, line_send, f_log)
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
                        Log.log_send(rec_ip, rec_p, line_send, f_log)
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
                        Log.log_send(rec_ip, rec_p, line_send, f_log)
                        self.wfile.write(line_send + "\r\n")

                    # Si la petición no está bien formada
                    else:
                        line_send = 'SIP/2.0 400 Bad Request\r\n'
                        Log.log_send(rec_ip, rec_p, line_send, f_log)
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
                            sock1 = socket.AF_INET
                            sock2 = socket.SOCK_DGRAM
                            my_socket = socket.socket(sock1, sock2)
                            sock3 = socket.SOL_SOCKET
                            sock4 = socket.SO_REUSEADDR
                            my_socket.setsockopt(sock3, sock4, 1)
                            my_socket.connect((ip_send, p_send))
                            Log.log_send(ip_send, p_send, line, f_log)
                            my_socket.send(line + '\r\n')

                            # Si es INVITE o BYE espero recibir
                            if not metodo == "ACK":
                                # Error si el servidor no está lanzado
                                try:
                                    # Recibo respuesta
                                    data = my_socket.recv(1024)
                                    Log.log_rec(ip_send, p_send, data, f_log)
                                    # Lo reenvío al cliente
                                    Log.log_send(rec_ip, rec_p, data, f_log)
                                    self.wfile.write(data + "\r\n")
                                except socket.error:
                                    line_log = "Error: No server listening at "
                                    line_log += dicc[name][0] + " port "
                                    line_log += str(p_send) + "\r\n"
                                    print line_log
                                    # log
                                    log = open(f_log, 'a')
                                    log.write(form_log + ' ' + line_log)
                                    log.close()
                                    # Le envío un 400 Bad Request al cliente
                                    l_send = 'SIP/2.0 400 Bad Request\r\n'
                                    Log.log_send(rec_ip, rec_p, l_send, f_log)
                                    self.wfile.write(l_send + "\r\n")
                                    break

                        # Si no está registrado o sí lo estaba pero ha expirado
                        else:
                            line_send = 'SIP/2.0 404 User Not Found\r\n'
                            Log.log_send(rec_ip, rec_p, line_send, f_log)
                            self.wfile.write(line_send + "\r\n")

                    # Si la petición no está bien formada
                    else:
                        line_send = 'SIP/2.0 400 Bad Request\r\n'
                        Log.log_send(rec_ip, rec_p, line_send, f_log)
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
            day_t_now1 = time.strftime(formato, time_now1)
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
    """
    dicc = {}
    formato = '%Y-%m-%d %H:%M:%S'
    # log, Herencia del cliente
    Log = Log()
    f_log = xml["log_path"]
    form_log = time.strftime('%Y%m%d%H%M%S')

    """
    SOCKET
    """
    server_n = xml["server_name"]
    server_ip = xml["server_ip"]
    if server_ip == "":
        server_ip = "127.0.0.1"
    server_p = int(xml["server_puerto"])

    try:
        inicio = "Server " + server_n + " listening at port "
        inicio += str(server_p) + "...\r\n"
        print "\n" + inicio
        # Leemos la base de datos de usuarios registrados
        txt = Registered()
        txt.leer_registered()
        # log
        log = open(f_log, 'a')
        log.write(form_log + ' ' + 'Starting...\r\n')
        log.close()
        # Creamos servidor de eco y escuchamos
        serv = SocketServer.UDPServer((server_ip, server_p), SipHandler)
        serv.serve_forever()
    except(KeyboardInterrupt):
        # log
        log = open(f_log, 'a')
        log.write(form_log + ' ' + '...Finishing.\r\n\r\n')
        log.close()
        print "\nTerminando proxy..."
        print "\nFin.\r\n"

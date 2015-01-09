#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa User Agent Client (UAC)
"""
import socket
import sys
import time
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class Log():
    """
    Guardar mensajes de depuración de envío en .log
    """
    def log_send(self, ip, puerto, line_send, fich):
        log = open(fich, 'a')
        send_to = "Sent to " + ip + ":" + str(puerto)
        print "\n" + send_to
        line_log = send_to + ": " + line_send.replace('\r\n', ' ') + '\r\n'
        log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)
        log.close()
        print '\nEnviando: ' + line_send

    """
    Guardar mensajes de depuración de recibo en .log
    """
    def log_rec(self, ip, puerto, line_rec, fich):
        log = open(fich, 'a')
        rec_from = 'Received from ' + ip + ":" + str(puerto)
        print "\n" + rec_from
        line_log = rec_from + ": " + line_rec.replace('\r\n', ' ') + '\r\n'
        log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)
        log.close()
        print "\nRecibido -- " + line_rec


class XMLHandler(ContentHandler):
    """
    LEER EL FICHERO XML
    """
    def __init__(self):
        self.diccionario = {}
        self.atributos = {
            'account': ['username'],
            'uaserver': ['ip', 'puerto'],
            'rtpaudio': ['puerto'],
            'regproxy': ['ip', 'puerto'],
            'log': ['path'],
            'audio': ['path']
        }

    def startElement(self, tag, attrs):
        if tag in self.atributos:
            for atributo in self.atributos[tag]:
                elemento = tag + "_" + atributo
                self.diccionario[elemento] = attrs.get(atributo, "")

    def get_tags(self):
        return self.diccionario


if __name__ == "__main__":
    """
    ERRORES EN LA LÍNEA DE COMANDOS
    """
    # Número de elementos introducidos
    if len(sys.argv) != 4:
        print "Usage: python uaclient.py config method option"
        raise SystemExit

    # CONFIG, METODO y OPCION
    CONFIG = sys.argv[1]
    METODO = sys.argv[2].upper()
    OPCION = sys.argv[3]

    # Errores en los valores: CONFIG, METODO
    try:
        CONFIG.split(".")[1]
    except IndexError:
        print "Usage: python uaclient.py config method option"
        raise SystemExit

    if not CONFIG.split(".")[1] == "xml":
        print "Usage: python uaclient.py config method option"
        raise SystemExit

    metodos_SIP = ("REGISTER", "INVITE", "BYE")

    if METODO not in metodos_SIP:
        print "Usage: python uaclient.py config method option"
        raise SystemExit

    # Errores en OPCION dependiendo del METODO
    if METODO == "REGISTER":
        try:
            OPCION = int(OPCION)
        except ValueError:
            print "Usage: python uaclient.py config method option"
            raise SystemExit

    elif METODO == "INVITE" or "BYE":
        try:
            OPCION.split("@")[1]
        except IndexError:
            print "Usage: python uaclient.py config method option"
            raise SystemExit

        if OPCION.split("@")[1] == "":
            print "Usage: python uaclient.py config method option"
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
        print "Usage: python uaclient.py config method option"
        raise SystemExit
    xml = sHandler.get_tags()

    """
    ENVIO AL SERVER
    """
    print '\nStarting...'

    # log
    Log = Log()
    f_log = xml["log_path"]
    form_log = time.strftime('%Y%m%d%H%M%S')

    # Contenido que vamos a enviar dependiendo del metodo
    line_send = METODO + " sip:"
    prox_ip = xml["regproxy_ip"]
    prox_p = int(xml["regproxy_puerto"])

    if METODO == "REGISTER":
        line_send += xml["account_username"] + ":" + xml["uaserver_puerto"]
        line_send += " SIP/2.0\r\n"
        line_send += "Expires: " + str(OPCION) + "\r\n"
        Log.log_send(prox_ip, prox_p, line_send, f_log)

    if METODO == "INVITE":
        line_send += OPCION + " SIP/2.0\r\n"
        line_send += "Content-Type: application/sdp\r\n\r\n"
        line_send += "v=0\r\n"
        line_send += "o=" + xml["account_username"] + " "
        uaserver_ip = xml["uaserver_ip"]
        if uaserver_ip == "":
            uaserver_ip = "127.0.0.1"
        line_send += uaserver_ip + "\r\n"
        line_send += "s=sesion_uac\r\n" + "t=0\r\n"
        line_send += "m=audio " + xml["rtpaudio_puerto"] + " RTP\r\n"
        Log.log_send(prox_ip, prox_p, line_send, f_log)

    if METODO == "BYE":
        line_send += OPCION + " SIP/2.0\r\n"
        Log.log_send(prox_ip, prox_p, line_send, f_log)

    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((prox_ip, int(prox_p)))
    my_socket.send(line_send + '\r\n')

    # Error si el servidor no está lanzado
    try:
        data = my_socket.recv(1024)
    except socket.error:
        line_log = "Error: No server listening at " + prox_ip
        line_log += " port " + str(prox_p) + "\r\n"
        print line_log
        # log
        log = open(f_log, 'a')
        log.write(form_log + ' ' + line_log)
        log.close()
        raise SystemExit

    # Recibo respuesta
    Log.log_rec(prox_ip, prox_p, data, f_log)
    data_serv = data.split('\r\n')

    # Si recibe esos códigos, envía el ACK y el audio RTP
    if METODO == 'INVITE':
        if data_serv[0] == 'SIP/2.0 100 Trying':
            if data_serv[2] == 'SIP/2.0 180 Ringing':
                if data_serv[4] == 'SIP/2.0 200 OK':
                    # Envio el ACK
                    line_send = "ACK sip:" + OPCION + " SIP/2.0\r\n"
                    Log.log_send(prox_ip, prox_p, line_send, f_log)
                    my_socket.send(line_send + '\r\n')
                    # Envio RTP
                    try:
                        # Busco en el sdp recibido la ip y el puerto
                        SDP_uas = data_serv[7:]
                        for linea in range(len(SDP_uas)):
                            cabecera = SDP_uas[linea].split("=")
                            if cabecera[0] == "o":
                                rtp_ip = cabecera[1].split(" ")[1]
                            elif cabecera[0] == "m":
                                rtp_p = cabecera[1].split(" ")[1]
                        # run: lo que se ha de ejecutar en la shell
                        run = './mp32rtp -i ' + rtp_ip + " -p " + rtp_p
                        run += " < " + xml["audio_path"]
                        print "Vamos a ejecutar", run
                        os.system(run)
                        line_send = "RTP audio\r\n"
                        Log.log_send(rtp_ip, rtp_p, line_send, f_log)
                        print "\r\nEl fichero de audio ha finalizado\r\n\r\n"
                    except IndexError:
                        print "\r\nError, SDP recibido incorrecto\r\n\r\n"

    # Cerramos el socket
    print "Terminando socket..."
    my_socket.close()
    print "\nFin.\r\n"

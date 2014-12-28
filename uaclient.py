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

"""
LEER EL FICHERO XML
"""
class XMLHandler(ContentHandler):

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

    if not METODO in metodos_SIP:
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
    # log
    log = open(xml["log_path"], 'a')
    print '\nStarting...'
    log.write("\r\n" + time.strftime('%Y%m%d%H%M%S') + ' ' + 'Starting...\r\n')
    send_to = "Sent to " + xml["regproxy_ip"] + ":" + xml["regproxy_puerto"]
    print "\n" + send_to

    # Contenido que vamos a enviar dependiendo del metodo
    line_send = METODO + " sip:"

    if METODO == "REGISTER":
        line_send += xml["account_username"] + ":" + xml["uaserver_puerto"]
        line_send += " SIP/2.0\r\n"
        line_send += "Expires: " + str(OPCION) + "\r\n"
        # log
        line_log = send_to + ": " + line_send.replace('\r\n', ' ') + '\r\n'
        log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)
    if METODO == "INVITE":
        line_send += OPCION + " SIP/2.0\r\n"
                        # ---> bien espacios ahí?
        line_send += "Content-Type: application/sdp\r\n\r\n"
        line_send += "v=0\r\n" 
        line_send += "o=" + xml["account_username"] + " " + xml["uaserver_ip"] + "\r\n" 
        line_send += "s=sesion_uac\r\n" + "t=0\r\n" 
        line_send += "m=audio " + xml["rtpaudio_puerto"] + " RTP\r\n"
        # log
        line_log = send_to + ": " + line_send.replace('\r\n', ' ') + '\r\n'
        log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)
    if METODO == "BYE":
        line_send += OPCION + " SIP/2.0\r\n"
        # log
        line_log = send_to + ": " + line_send.replace('\r\n', ' ') + '\r\n'
        log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)

    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((xml["regproxy_ip"], int(xml["regproxy_puerto"])))
    
    my_socket.send(line_send + '\r\n')
    print "\nEnviando: " + line_send

    # Error si el servidor no está lanzado
    try:
        data = my_socket.recv(1024)
    except socket.error:
        line_log = "Error: No server listening at " + xml["regproxy_ip"]
        line_log += " port " + str(xml["regproxy_puerto"]) + "\r\n"
        print line_log
        # log
        log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)
        raise SystemExit

    # Recibo respuesta
    # log
    rec_from = "Received from " + xml["regproxy_ip"] + ":" + xml["regproxy_puerto"]
    print "\n" + rec_from
    line_log = rec_from + ": " + data.replace('\r\n', ' ') + '\r\n'
    log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)
    print "\nRecibido -- " + data

    data_serv = data.split('\r\n')

    # Si recibe esos códigos, envía el ACK y el audio RTP
    if METODO == 'INVITE':
        if data_serv[0] == 'SIP/2.0 100 Trying':
            if data_serv[2] == 'SIP/2.0 180 Ringing':
                if data_serv[4] == 'SIP/2.0 200 OK':
                    line_send = "ACK sip:" + OPCION + " SIP/2.0\r\n"
                    # log
                    send_to = "Sent to " + xml["regproxy_ip"] + ":" + xml["regproxy_puerto"]
                    print send_to
                    line_log = send_to + ": " + line_send.replace('\r\n', ' ') + '\r\n'
                    log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)
                    my_socket.send(line_send + '\r\n')
                    print "\nEnviando: " + line_send

                    # ENVIO RTP tras el ACK
                                    # ---> esto es así??
                    ip_rtp = data_serv[8].split(' ')[1]
                    puerto_rtp = data_serv[11].split(' ')[1]
                    # run: lo que se ha de ejecutar en la shell
                                    # ---> lo manda directamente no???
                    run = './mp32rtp -i ' + ip_rtp + " -p " + puerto_rtp
                    run += " < " + xml["audio_path"]
                    print "Vamos a ejecutar", run
                    os.system(run)
                    # log
                    line_send = "Sent to " + ip_rtp + ':' + str(puerto_rtp)
                    print line_send
                    line_log = line_send + ": " + "RTP audio\r\n"
                    log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)
                    print "\r\nEl fichero de audio ha finalizado\r\n\r\n"    

        # ---> da igual que nos llegue o no un 200 ok del register o el bye no?

    # Cerramos el socket
    # log
    line_log = "Finishing.\r\n"
    log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)
    my_socket.close()
    print line_log

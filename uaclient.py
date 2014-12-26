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
                    # ---> que pasa si expires es 0?
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
    # Contenido que vamos a enviar dependiendo del metodo
    LINE = METODO + " sip:"

    if METODO == "REGISTER":
                         # ---> bien el puerto??
        LINE += xml["account_username"] + ":" + xml["uaserver_puerto"]
        LINE += " SIP/2.0\r\n"
        LINE += "Expires: " + str(OPCION) + "\r\n"
    if METODO == "INVITE":
        LINE += OPCION + " SIP/2.0\r\n"
                        # ---> bien espacios ahí?
        LINE += "Content-Type: application/sdp\r\n\r\n"
        LINE += "v=0\r\n" 
                        # ---> que ip? la de proxy o la de server?
        LINE += "o=" + xml["account_username"] + " " + xml["uaserver_ip"] + "\r\n" 
        LINE += "s=sesion_uac\r\n" + "t=0\r\n" 
        LINE += "m=audio " + xml["rtpaudio_puerto"] + " RTP\r\n"
    if METODO == "BYE":
                    # ---> q pasa si no ha acado el rtp? 
                    # ---> y como contemplo aqui q me llegue un bye del server?
        LINE += OPCION + " SIP/2.0\r\n"

    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        # ---> error si el proxy o el server no están conectados?
    my_socket.connect((xml["regproxy_ip"], int(xml["regproxy_puerto"])))

    print "\nEnviando: " + LINE
    my_socket.send(LINE + '\r\n')

    # Error si el servidor no está lanzado
    try:
        data = my_socket.recv(1024)
    except socket.error:
        print "Error: No server listening at " + xml["regproxy_ip"] + " port " + str(xml["regproxy_puerto"]) + "\r\n"
        raise SystemExit

    # Recibo respuesta
    print 'Recibido -- ', data

                        #---> separo por solo un \r\n?
    data_serv = data.split('\r\n')


    # Si recibe esos códigos, envía el ACK y el audio RTP
    if METODO == 'INVITE':
        if data_serv[0] == 'SIP/2.0 100 Trying':
            if data_serv[1] == 'SIP/2.0 180 Ringing':
                if data_serv[2] == 'SIP/2.0 200 OK':
                    LINE = "ACK sip:" + OPCION + " SIP/2.0\r\n"
                    print "Enviando: " + LINE
                    my_socket.send(LINE + '\r\n')
                    # ENVIO RTP tras el ACK
                    ip_rtp = data_serv[6].split(' ')[1]
                                #---> eliminar esos print
                    print "ESTO ES LA IP_RTP" + ip_rtp
                    puerto_rtp = data_serv[9].split(' ')[1]
                    print "ESTO ES EL PUERTO RTP" + ip_rtp
                    # run: lo que se ha de ejecutar en la shell
                    run = './mp32rtp -i ' + ip_rtp + " -p " + puerto_rtp
                    run += " < " + xml["audio_path"]
                    print "Vamos a ejecutar", run
                    os.system(run)
                    print "\r\nEl fichero de audio ha finalizado\r\n\r\n"    
    # Si le ha enviado un BYE y recibe ese código, se finaliza la conexión
    elif METODO == 'BYE':
        if data_serv[0] == 'SIP/2.0 200 OK':
            print "Se cierra la conexión con el servidor...\r\n"
    # Si le ha enviado un REGISTER y recibe ese código, se finaliza la conexión
        # dependiendo del valor del expire
    elif METODO == 'REGISTER':
        if OPCION == "0":
            print "Se cierra la conexión con el servidor...\r\n"
    else:
                #---> log
        print "Linea log"   

    # Cerramos el socket
    print "Terminando socket..."
    my_socket.close()
    print "\nFin.\r\n"

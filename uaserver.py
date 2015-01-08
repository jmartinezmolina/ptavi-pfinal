#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa User Agent Server (UAS)
"""
import SocketServer
import sys
import os
import time
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaclient import XMLHandler

"""
CLASE ECHO HANDLER
"""
SDP_uac_ip = ""
SDP_uac_puerto = 0


class EchoHandler(SocketServer.DatagramRequestHandler):
    """
    Echo server class
    """
    def handle(self):
        while 1:
            # Leyendo línea a línea lo que nos envía el proxy del cliente
            line = self.rfile.read()
            if not line:
                break
            rec_ip = self.client_address[0]
            rec_puerto = self.client_address[1]
            self.log_rec(rec_ip, rec_puerto, line)
            # Ver si el método llegado es correcto
            metodo = line.split()[0]
            metodos_SIP = ("INVITE", "BYE", "ACK")

            if metodo not in metodos_SIP:
                line_send = 'SIP/2.0 405 Method Not Allowed\r\n'
                self.log_send(rec_ip, rec_puerto, line_send)
                self.wfile.write(line_send + "\r\n")

            else:
                # Ver si la petición está bien formada
                protocolo = line.split()[1].split(':')[0]
                direc = line.split()[1].split(':')[1]
                sip_v = line.split()[2]

                if protocolo == "sip" and "@" in direc and sip_v == "SIP/2.0":

                    # Responder según el método recibido
                    if metodo == 'INVITE':
                        # Creamos el SDP a mandar con el "200 OK"
                        SDP_uas = "Content-Type: application/sdp\r\n\r\n"
                        SDP_uas += "v=0\r\n"
                        SDP_uas += "o=" + xml["account_username"] + " "
                        SDP_uas += xml["uaserver_ip"] + "\r\n"
                        SDP_uas += "s=sesion_uas\r\n" + "t=0\r\n"
                        SDP_uas += "m=audio " + xml["rtpaudio_puerto"]
                        SDP_uas += " RTP\r\n"
                        # Llega SDP del cliente, obtenemos los valores deseados
                        try:
                            SDP_uac = line.split('\r\n')[3:]
                            # Busco en el sdp recibido la ip y el puerto
                            for cab in range(len(SDP_uac)):
                                if SDP_uac[cab].split("=")[0] == "o":
                                    ip_rtp = SDP_uac[cab].split("=")[1].split(" ")[1]
                                elif SDP_uac[cab].split("=")[0] == "m":
                                    puerto_rtp = SDP_uac[cab].split("=")[1].split(" ")[1]
                            # Guardo la ip y puerto para poder acceder más tarde
                            Lista_SDP_uac = [ip_rtp, puerto_rtp]
                            Dicc_SDP_uac['key'] = Lista_SDP_uac
                            # Respondo al Invite
                            line_send = 'SIP/2.0 100 Trying\r\n'
                            self.log_send(rec_ip, rec_puerto, line_send)
                            self.wfile.write(line_send + "\r\n")
                            line_send = 'SIP/2.0 180 Ringing\r\n'
                            self.log_send(rec_ip, rec_puerto, line_send)
                            self.wfile.write(line_send + "\r\n")
                            line_send = 'SIP/2.0 200 OK\r\n' + SDP_uas
                            self.log_send(rec_ip, rec_puerto, line_send)
                            self.wfile.write(line_send + "\r\n")
                        except IndexError:
                            line_send = 'SIP/2.0 400 Bad Request\r\n'
                            self.log_send(rec_ip, rec_puerto, line_send)
                            self.wfile.write(line_send + "\r\n")

                    elif metodo == 'ACK':
                                # --> no funcionaaaaaaaaaaaa
                        # ENVIO RTP
                        ip = Dicc_SDP_uac['key'][0]
                        puerto = str(Dicc_SDP_uac['key'][1])
                        # run: lo que se ha de ejecutar en la shell
                        run = './mp32rtp -i ' + ip + " -p " + puerto
                        run += " < " + xml["audio_path"]
                        print "Vamos a ejecutar", run
                        os.system(run)
                        line_send = "RTP audio\r\n"
                        self.log_send(ip, puerto, line_send)
                        print "\r\nEl fichero de audio ha finalizado\r\n\r\n"

                    elif metodo == 'BYE':
                        line_send = 'SIP/2.0 200 OK\r\n'
                        self.log_send(rec_ip, rec_puerto, line_send)
                        self.wfile.write(line_send + "\r\n")

                else:
                    line_send = 'SIP/2.0 400 Bad Request\r\n'
                    self.log_send(rec_ip, rec_puerto, line_send)
                    self.wfile.write(line_send + "\r\n")

    """
    Guardar mensajes de depuración de envío en .log
    """
    def log_send(self, ip, puerto, line_send):
        log = open(xml["log_path"], 'a')
        send_to = "Sent to " + ip + ":" + str(puerto)
        print "\n" + send_to
        line_log = send_to + ": " + line_send.replace('\r\n', ' ') + '\r\n'
        log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)
        print '\nEnviando: ' + line_send

    """
    Guardar mensajes de depuración de recibo en .log
    """
    def log_rec(self, ip, puerto, line_rec):
        log = open(xml["log_path"], 'a')
        rec_from = 'Received from ' + ip + ":" + str(puerto)
        print "\n" + rec_from
        line_log = rec_from + ": " + line_rec.replace('\r\n', ' ') + '\r\n'
        log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)
        print "\nRecibido -- " + line_rec


if __name__ == "__main__":
    """
    ERRORES EN LA LÍNEA DE COMANDOS
    """
    # Número de elementos introducidos
    if len(sys.argv) != 2:
        print "Usage: python uaserver.py config"
        raise SystemExit

    # Error en el valor CONFIG
    CONFIG = sys.argv[1]

    try:
        CONFIG.split(".")[1]
    except IndexError:
        print "Usage: python uaserver.py config"
        raise SystemExit

    if not CONFIG.split(".")[1] == "xml":
        print "Usage: python uaserver.py config"
        raise SystemExit

    """
    PARSER CON LOS VALORES DE XML
    """
    # Herencia del cliente
    parser = make_parser()
    sHandler = XMLHandler()
    parser.setContentHandler(sHandler)
    try:
        parser.parse(open(CONFIG))
    except IOError:
        print "Usage: python uaserver.py config"
        raise SystemExit
    xml = sHandler.get_tags()

    """
    """
    Dicc_SDP_uac = {}

    """
    SOCKET
    """
    server_ip = xml["uaserver_ip"]
    if server_ip == "":
        server_ip = "127.0.0.1"
    server_p = int(xml["uaserver_puerto"])
    try:
        print '\nListening...'
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
        print "\nTerminando server..."
        print "\nFin.\r\n"

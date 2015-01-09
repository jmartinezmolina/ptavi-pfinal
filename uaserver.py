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
from uaclient import Log


class EchoHandler(SocketServer.DatagramRequestHandler):
    """
    CLASE ECHO HANDLER
    """
    def handle(self):
        while 1:
            # Leyendo línea a línea lo que nos envía el proxy del cliente
            line = self.rfile.read()
            if not line:
                break
            rec_ip = self.client_address[0]
            rec_puerto = self.client_address[1]
            Log.log_rec(rec_ip, rec_puerto, line, f_log)
            # Ver si el método llegado es correcto
            metodo = line.split()[0]
            metodos_SIP = ("INVITE", "BYE", "ACK")

            if metodo not in metodos_SIP:
                line_send = 'SIP/2.0 405 Method Not Allowed\r\n'
                Log.log_send(rec_ip, rec_puerto, line_send, f_log)
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
                            for linea in range(len(SDP_uac)):
                                cabecera = SDP_uac[linea].split("=")
                                if cabecera[0] == "o":
                                    rtp_ip = cabecera[1].split(" ")[1]
                                elif cabecera[0] == "m":
                                    rtp_p = cabecera[1].split(" ")[1]
                            # Guardo ip y puerto para acceder más tarde
                            Lista_SDP_uac = [rtp_ip, rtp_p]
                            Dicc_SDP_uac['key'] = Lista_SDP_uac
                            # Respondo al Invite
                            line_send = 'SIP/2.0 100 Trying\r\n'
                            Log.log_send(rec_ip, rec_puerto, line_send, f_log)
                            self.wfile.write(line_send + "\r\n")
                            line_send = 'SIP/2.0 180 Ringing\r\n'
                            Log.log_send(rec_ip, rec_puerto, line_send, f_log)
                            self.wfile.write(line_send + "\r\n")
                            line_send = 'SIP/2.0 200 OK\r\n' + SDP_uas
                            Log.log_send(rec_ip, rec_puerto, line_send, f_log)
                            self.wfile.write(line_send + "\r\n")
                        except IndexError:
                            line_send = 'SIP/2.0 400 Bad Request\r\n'
                            Log.log_send(rec_ip, rec_puerto, line_send, f_log)
                            self.wfile.write(line_send + "\r\n")

                    elif metodo == 'ACK':
                        # Envio RTP
                        rtp_ip = Dicc_SDP_uac['key'][0]
                        rtp_p = str(Dicc_SDP_uac['key'][1])
                        # run: lo que se ha de ejecutar en la shell
                        run = './mp32rtp -i ' + rtp_ip + " -p " + rtp_p
                        run += " < " + xml["audio_path"]
                        print "Vamos a ejecutar", run
                        os.system(run)
                        line_send = "RTP audio\r\n"
                        Log.log_send(rtp_ip, rtp_p, line_send, f_log)
                        print "\r\nEl fichero de audio ha finalizado\r\n\r\n"

                    elif metodo == 'BYE':
                        line_send = 'SIP/2.0 200 OK\r\n'
                        Log.log_send(rec_ip, rec_puerto, line_send, f_log)
                        self.wfile.write(line_send + "\r\n")

                else:
                    line_send = 'SIP/2.0 400 Bad Request\r\n'
                    Log.log_send(rec_ip, rec_puerto, line_send, f_log)
                    self.wfile.write(line_send + "\r\n")


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
    # log, Herencia del cliente
    Log = Log()
    f_log = xml["log_path"]
    form_log = time.strftime('%Y%m%d%H%M%S')

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
        log = open(f_log, 'a')
        log.write(form_log + ' ' + 'Starting...\r\n')
        log.close()
        # Creamos servidor de eco y escuchamos
        serv = SocketServer.UDPServer((server_ip, server_p), EchoHandler)
        serv.serve_forever()
    except(KeyboardInterrupt):
        # log
        log = open(f_log, 'a')
        log.write(form_log + ' ' + '...Finishing.\r\n\r\n')
        log.close()
        print "\nTerminando server..."
        print "\nFin.\r\n"

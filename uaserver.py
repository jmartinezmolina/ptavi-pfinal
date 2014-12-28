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

            # log
            log = open(xml["log_path"], 'a')
            rec_from = 'Received from ' + rec_ip + ":" + str(rec_puerto)
            print "\n" + rec_from
            line_log = rec_from + ": " + line.replace('\r\n', ' ') + '\r\n'
            log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)
            print "\nRecibido -- " + line
            
            # Ver si el método llegado es correcto
            metodo = line.split()[0]
            metodos_SIP = ("INVITE", "BYE", "ACK")

            if not metodo in metodos_SIP:
                # log
                send_to = "Sent to " + rec_ip + ":" + str(rec_puerto)
                print "\n" + send_to
                line_send = 'SIP/2.0 405 Method Not Allowed\r\n'
                line_log = send_to + ": " + line_send.replace('\r\n', ' ') + '\r\n'
                log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)
                self.wfile.write(line_send + "\r\n")
                print '\nEnviando: ' + line_send
            
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
                        SDP_uas += "o=" + xml["account_username"] + " " + xml["uaserver_ip"] + "\r\n" 
                        SDP_uas += "s=sesion_uas\r\n" + "t=0\r\n" 
                        SDP_uas += "m=audio " + xml["rtpaudio_puerto"] + " RTP\r\n"

                        # Llega SDP del cliente, obtenemos los valores deseados
                        SDP_uac = line.split()[3:]

                        # for cab in SDP_uac:
                        #    if cab.split("=")[0] == "o":
                        #        uac_o_server_ip = cab.split("=")[1]
                        #    elif cab.split("=")[0] == "m":
                        #        uac_m_rtp_puerto = cab + 1

                                #---> puedo dar por hecho eso? q lo mande como diccionario? for?
                        Lista_SDP_uac = [SDP_uac[-6], SDP_uac[-2]]
                        Dicc_SDP_uac['key'] = Lista_SDP_uac

                        # log
                        send_to = "Sent to " + rec_ip + ":" + str(rec_puerto)
                        print "\n" + send_to
                        line_send = 'SIP/2.0 100 Trying\r\n'
                        line_log = send_to + ": " + line_send.replace('\r\n', ' ') + '\r\n'
                        log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)
                                                   # ---> bien dos barra n no?
                        self.wfile.write(line_send + "\r\n")
                        print '\nEnviando: ' + line_send
                        # log
                        send_to = "Sent to " + rec_ip + ":" + str(rec_puerto)
                        print "\n" + send_to
                        line_send = 'SIP/2.0 180 Ringing\r\n'
                        line_log = send_to + ": " + line_send.replace('\r\n', ' ') + '\r\n'
                        log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)
                        self.wfile.write(line_send + "\r\n")
                        print '\nEnviando: ' + line_send
                        # log
                        send_to = "Sent to " + rec_ip + ":" + str(rec_puerto)
                        print "\n" + send_to
                        line_send = 'SIP/2.0 200 OK\r\n' + SDP_uas + "\r\n"
                        line_log = send_to + ": " + line_send.replace('\r\n', ' ') + '\r\n'
                        log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)
                        self.wfile.write(line_send + "\r\n")
                        print '\nEnviando: ' + line_send

                    elif metodo == 'ACK':
                        # ENVIO RTP
                        ip = Dicc_SDP_uac['key'][0]
                        puerto = str(Dicc_SDP_uac['key'][1])
                        # run: lo que se ha de ejecutar en la shell
                        run = './mp32rtp -i ' + ip + " -p " + puerto 
                        run += " < " + xml["audio_path"]
                        print "Vamos a ejecutar", run
                        os.system(run)
                        # log
                        line_send = "Sent to " + ip + ':' + str(puerto)
                        print line_send
                        line_log = line_send + ": " + "RTP audio\r\n"
                        log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)
                        print "\r\nEl fichero de audio ha finalizado\r\n\r\n" 

                    elif metodo == 'BYE':
                                    #---> SDP también en el BYE?
                        # log
                        send_to = "Sent to " + rec_ip + ":" + str(rec_puerto)
                        print "\n" + send_to
                        line_send = 'SIP/2.0 200 OK\r\n'
                        line_log = send_to + ": " + line_send.replace('\r\n', ' ') + '\r\n'
                        log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)
                        self.wfile.write(line_send + "\r\n")
                        print '\nEnviando: ' + line_send
                
                else:
                    # log
                    send_to = "Sent to " + rec_ip + ":" + str(rec_puerto)
                    print "\n" + send_to
                    line_send = 'SIP/2.0 400 Bad Request\r\n'
                    line_log = send_to + ": " + line_send.replace('\r\n', ' ') + '\r\n'
                    log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + line_log)
                    self.wfile.write(line_send + "\r\n")
                    print '\nEnviando: ' + line_send


if __name__ == "__main__":
    """
    ERRORES EN LA LÍNEA DE COMANDOS
    """
    # Número de elementos introducidos
    if len(sys.argv) != 2:
        print "Usage: python uaserver.py config"
        raise SystemExit

    #Error en el valor CONFIG
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
    # log
    log = open(xml["log_path"], 'a')
    print '\nListening...'
    log.write(time.strftime('%Y%m%d%H%M%S') + ' ' + 'Listening...\r\n')
    log.close()
    # Creamos servidor de eco y escuchamos
    serv = SocketServer.UDPServer((xml["uaserver_ip"], int(xml["uaserver_puerto"])), EchoHandler)
    serv.serve_forever()

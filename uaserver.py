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
            print "El cliente nos manda " + line
            cliente_ip = self.client_address[0]
            cliente_puerto = self.client_address[1] 
            
            # Ver si el método llegado es correcto
            metodo = line.split()[0]
            metodos_SIP = ("INVITE", "BYE", "ACK")
            if not metodo in metodos_SIP:
                self.wfile.write('SIP/2.0 405 Method Not Allowed\r\n\r\n')
                print 'Enviando: SIP/2.0 405 Method Not Allowed\r\n\r\n'
            else:
                # Ver si la petición está bien formada
                protocolo = line.split()[1].split(':')[0]
                direc = line.split()[1].split(':')[1]
                sip_v = line.split()[2]
                if protocolo == "sip" and "@" in direc and sip_v == "SIP/2.0":
                    
                    # Creamos el SDP a mandar con el "200 OK"
                    SDP_uas = "Content-Type: application/sdp\r\n\r\n"
                    SDP_uas += "v=0\r\n" 
                            # ---> que ip? la de proxy o la de server?
                    SDP_uas += "o=" + xml["account_username"] + " " + xml["uaserver_ip"] + "\r\n" 
                    SDP_uas += "s=sesion_uas\r\n" + "t=0\r\n" 
                    SDP_uas += "m=audio " + xml["rtpaudio_puerto"] + " RTP\r\n"

                    # Responder según el método recibido
                    if metodo == 'INVITE':
                        # Llega SDP del cliente, obtenemos los valores deseados
                        SDP_uac = line.split()[3:]

                        for cab in SDP_uac:
                            if cab.split("=")[0] == "o":
                                uac_o_server_ip = cab + 1
                            elif cab.split("=")[0] == "m":
                                uac_m_rtp_puerto = cab + 1

                                #---> puedo dar por hecho eso? q lo mande como diccionario? for?
                        #uac_rtp_puerto = SDP_uac[-2]
    
                        self.wfile.write('SIP/2.0 100 Trying\r\n\r\n')
                        print 'Enviando: ' + 'SIP/2.0 100 Trying\r\n\r\n'
                        self.wfile.write('SIP/2.0 180 Ringing\r\n\r\n')
                        print 'Enviando: ' + 'SIP/2.0 180 Ringing\r\n\r\n'
                        LINE = "SIP/2.0 200 OK\r\n" + SDP_uas + "\r\n\r\n"
                        self.wfile.write(LINE)
                        print 'Enviando: ' + LINE
                    elif metodo == 'ACK':
                        # run: lo que se ha de ejecutar en la shell
                                    #---> ip del proxy o del q le llega la petición?
                                    #---> ip_clt = str(self.client_address[0])
                        run = './mp32rtp -i ' + uac_o_server_ip + " -p " + uac_m_rtp_puerto 
                        run += " < " + xml["audio_path"]
                        print "Vamos a ejecutar", run
                        os.system(run)
                        print "\r\nEl fichero de audio ha finalizado\r\n\r\n"
                    elif metodo == 'BYE':
                        #---> SDP también en el BYE?
                        LINE = "SIP/2.0 200 OK\r\n" + SDP_uas + "\r\n\r\n"
                        self.wfile.write(LINE)
                        print 'Enviando: ' + LINE
                
                else:
                    self.wfile.write('SIP/2.0 400 Bad Request\r\n\r\n')
                    print 'Enviando: SIP/2.0 400 Bad Request\r\n\r\n'


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
    SOCKET
    """
    # Creamos servidor de eco y escuchamos
            # ---> q puerto ponemos? no es donde escucha tb el cliente q lo pasa en el register?
    serv = SocketServer.UDPServer(("", int(xml["uaserver_puerto"])), EchoHandler)
    print "\nListening...\r\n"
    serv.serve_forever()

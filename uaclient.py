#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# Práctica Final   JAVIER MARTINEZ MOLINA

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import socket
import sys
import os
import time


class XMLHandler(ContentHandler):


    def __init__(self):
        self.etiquetas = {'account': ['username', 'passwd'],
            'uaserver': ['ip', 'puerto'],
            'rtpaudio': ['puerto'],
            'regproxy': ['ip', 'puerto'],
            'log': ['path'],
            'audio': ['path']}
  
        self.list_etiquetas = []
        
        self.dic_etiq = {'account_username': '', 'account_passwd': '',
            'uaserver_ip': '', 'uaserver_puerto': '', 'rtpaudio_puerto': '',
            'regproxy_ip': '', 'regproxy_puerto': '', 'log_path': '',
            'audio_path': ''}


    def startElement(self, name, attrs):
        dic = {}
        if name in self.etiquetas:
            dic["name"] = name
            for atributo in self.etiquetas[name]:
                dic[atributo] = attrs.get(atributo, "")
            self.list_etiquetas.append(dic)
        for dic in self.list_etiquetas:
            for etiqueta in dic:
                if dic["name"] == 'account':
                    if etiqueta == "username":
                        self.dic_etiq['account_username'] = dic[etiqueta]
                    if etiqueta == "passwd":
                        self.dic_etiq['account_passwd'] = dic[etiqueta]
                if dic["name"] == 'uaserver':
                    if etiqueta == "ip":
                        self.dic_etiq['uaserver_ip'] = dic[etiqueta]
                    if etiqueta == "puerto":
                        self.dic_etiq['uaserver_puerto'] = dic[etiqueta]
                if dic["name"] == 'rtpaudio':
                    if etiqueta == "puerto":
                        self.dic_etiq['rtpaudio_puerto'] = dic[etiqueta]
                if dic["name"] == 'regproxy':
                    if etiqueta == "ip":
                        self.dic_etiq['regproxy_ip'] = dic[etiqueta]
                    if etiqueta == "puerto":
                        self.dic_etiq['regproxy_puerto'] = dic[etiqueta]
                if dic["name"] == 'log':
                    if etiqueta == "path":
                        self.dic_etiq['log_path'] = dic[etiqueta]
                if dic["name"] == 'audio':
                    if etiqueta == "path":
                        self.dic_etiq['audio_path'] = dic[etiqueta]


    def add_to_log(self, LOG_PATH, add):
        
        hora = str(time.strftime("%Y%m%d%H%M%S", time.gmtime()))
        recorte = add.split('\r\n')
        ' '.join(recorte)
        fich = open(LOG_PATH, "a")
        fich.write(hora + ' ' + recorte[0] + '...\r\n')


if __name__ == "__main__":

    list_metodo = ['INVITE', 'REGISTER', 'BYE']
    dic_info = {}

    #Comprobación de posibles excepciones
    if len(sys.argv) != 4:
        print 'Usage: python uaclient.py config method option'
        raise SystemExit

    if sys.argv[2].upper() not in list_metodo:
        print 'Usage: python uaclient.py config method option'
        raise SystemExit

    METODO = str(sys.argv[2]).upper()
    FICHERO = str(sys.argv[1])
    OPCION = str(sys.argv[3])
    
    parser = make_parser()
    chandler = XMLHandler()
    parser.setContentHandler(chandler)
    parser.parse(open(FICHERO))
    
    USERNAME = chandler.dic_etiq['account_username']
    UASERVER_IP = chandler.dic_etiq['uaserver_ip']
    UASERVER_PORT = int(chandler.dic_etiq['uaserver_puerto'])
    RTPAUDIO_PORT = int(chandler.dic_etiq['rtpaudio_puerto'])
    REGPROXY_IP = chandler.dic_etiq['regproxy_ip']
    REGPROXY_PORT = int(chandler.dic_etiq['regproxy_puerto'])
    LOG_PATH = chandler.dic_etiq['log_path']
    AUDIO_PATH = chandler.dic_etiq['audio_path']
    
    if not os.path.exists(LOG_PATH):
        print 'Usage: python uaserver.py config'
        raise SystemExit

    if not os.path.exists(AUDIO_PATH):
        print 'Usage: python uaserver.py config'
        raise SystemExit
    
    add = " Starting"
    chandler.add_to_log(LOG_PATH, add)

    if METODO == "REGISTER":
        try:
            int(OPCION)
        except ValueError:
            print 'Usage: python uaclient.py config REGISTER -time-expires-'
            raise SystemExit
            
        LINE = METODO + " sip:" + USERNAME + ":"
        LINE += str(UASERVER_PORT) + " SIP/2.0" + "\r\n\r\n"
        LINE = LINE + "Expires: " + OPCION + "\r\n\r\n"       

    if METODO == "INVITE":
        # Contenido que vamos a enviar
        LINE = METODO + " sip:" + OPCION + " SIP/2.0\r\n"
        LINE += "Content-Type: application/sdp\r\n\r\n"
        LINE += "v=0\r\n" + "o=" + USERNAME + " " + UASERVER_IP + "\r\n"
        LINE += "s=misesion\r\n" + "t=0\r\n" + "m=audio "
        LINE += str(RTPAUDIO_PORT) + " RTP"
    
    if METODO == "BYE":
        LINE = METODO + " sip:" + OPCION + " SIP/2.0\r\n\r\n"


    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((REGPROXY_IP, REGPROXY_PORT))

    try:
        #Envio del mensaje
        my_socket.send(LINE)
        add = " Send to " + str(REGPROXY_IP) + ":"
        add += str(REGPROXY_PORT) + ' ' + str(LINE)
        chandler.add_to_log(LOG_PATH, add)
        print "Enviando: " + LINE
        #Recibimos el mensaje
        data = my_socket.recv(1024)
        add = " Received from " + str(REGPROXY_IP) + ":"
        add += str(REGPROXY_PORT) + ' ' + str(data)
        chandler.add_to_log(LOG_PATH, add)
    except socket.error:
        port = str(REGPROXY_PORT)
        error = 'Error: No server listening at ' + REGPROXY_IP + ' port ' + port
        print error
        add = ' ' + str(error)
        chandler.add_to_log(LOG_PATH, add)
        raise SystemExit

    print 'Recibido -- \r\n\r\n', data
    
    if METODO == "INVITE":
        
        r_metodo = data.split("\r\n\r\n")
        if r_metodo[0] == "SIP/2.0 100 Trying":
            if r_metodo[1] == "SIP/2.0 180 Ringing":
                r_dos_ok = r_metodo[2].split('\r\n')
                if r_dos_ok[0] == "SIP/2.0 200 OK":
                    ack = "ACK sip:" + OPCION + " SIP/2.0\r\n\r\n"
                    my_socket.send(ack + "\r\n")
                    add = ' Send to ' + str(REGPROXY_IP) + ":"
                    add += str(REGPROXY_PORT) + ' ' + str(ack)
                    chandler.add_to_log(LOG_PATH, add)
                    list_palabras = data.split("\r\n")
                    for linea in list_palabras:
                        key_value = linea.split('=')
                        if len(key_value) == 2:
                            dic_info[key_value[0]] = key_value[1]
                    ip_client = dic_info['o'].split(' ')
                    port_rtp = dic_info['m'].split(' ')
                    os.system('chmod 755 mp32rtp')
                    run = './mp32rtp -i ' + ip_client[1] + ' -p '
                    run += port_rtp[1] + ' < ' + AUDIO_PATH
                    os.system(run)
                    print "ENVIO: " + ack

    print "Terminando socket..."
    my_socket.close()
    print "Fin."

#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
# PRÁCTICA Final --- JAVIER MARTÍNEZ MOLINA

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import SocketServer
import sys
import time
import uaclient
import socket

LIST_METODO = ['REGISTER', 'INVITE', 'BYE', 'ACK']


class XMLHandler(ContentHandler):
    

    def __init__(self):   

        self.etiquetas = {'server': ['name', 'ip',
 'puerto'],
            'database': ['path', 'passwdpath'],
            'log': ['path']}
  
        self.list_etiquetas = []
    
        self.dic_etiq = {'server_name': '', 'server_ip': '',
            'server_puerto': '', 'database_path': '', 
            'database_passwdpath': '', 'log_path': ''}
            

    def startElement(self, name, attrs):

        dic = {}
        if name in self.etiquetas:
            dic["nombre"] = name
            for atributo in self.etiquetas[name]:
                dic[atributo] = attrs.get(atributo, "")
            self.list_etiquetas.append(dic)
        for dic in self.list_etiquetas:
            for etiqueta in dic:
                if dic["nombre"] == 'server':
                    if etiqueta == 'name':
                        self.dic_etiq['server_name'] = dic[etiqueta]
                    if etiqueta == 'ip':
                        self.dic_etiq['server_ip'] = dic[etiqueta]
                    if etiqueta == 'puerto':
                        self.dic_etiq['server_puerto'] = dic[etiqueta]
                if dic["nombre"] == 'database':
                    if etiqueta == 'path':
                        self.dic_etiq['database_path'] = dic[etiqueta]
                    if etiqueta == 'passwdpath':
                        self.dic_etiq['database_passwdpath'] = dic[etiqueta]
                if dic["nombre"] == 'log':
                    if etiqueta == 'path':
                        self.dic_etiq['log_path'] = dic[etiqueta]


class SIPRegisterHandler(SocketServer.DatagramRequestHandler):
    
    dic_reg = {}
    
    def send_mensaje(self, ip_user, port_user, line):
    
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((ip_user, port_user))
        
        try:
            #Envio del mensaje
            my_socket.send(line + '\r\n')
            print "Enviando: " + line
            #Recibimos el mensaje
            data = my_socket.recv(1024)
        except socket.error:
            port = str(port_user)
            print 'Error: No server listening at ' + ip_user + ' port ' + port
            print error
            raise SystemExit
        self.wfile.write(data)
        print 'Recibido -- \r\n\r\n', data


    def register2file(self, DATABASE_PATH):
        """
        Base de datos de usuarios registrados
        """
        fich = open(DATABASE_PATH, "w")
        fich.write("User\t" + "IP\t" + "Port\t" + "Registro\t" + "Expires\r\n")
        for mail in self.dic_reg:
            expires = str(self.dic_reg[mail][1])
            t = str(time.time())
            datos = mail + "\t" + self.dic_reg[mail][0] + "\t"
            datos += self.dic_reg[mail][2] + "\t" + t + "\t" + expires  + "\r\n"
            fich.write(datos)
        fich.close()

    def handle(self):
        """
        Se comprueba el tipo de mensaje,la caducidad de los usuarios, se añade 
        al dic a los users válidos y se borra a los user con EXPIRES a 0.
        """
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            if not line:
                break
            else:
                control = line.find('sip:')
                control2 = line.find('@')
                control3 = line.find('SIP/2.0')
                #Comprobacion de estructura del mensaje recibido
                if control >= 0 and control2 >= 0 and control3 >= 0:
                    list_palabras = line.split()

                    if list_palabras[0] == "REGISTER":
                        #Compruebo mi dic para localizar posibles users EXPIRES
                        #y actualizo tanto el dic como la base de datos
                        if self.dic_reg:
                            tiempo_actual = time.time()
                            for user in self.dic_reg.keys():
                                if self.dic_reg[user][1] <= tiempo_actual:
                                    del self.dic_reg[user]
                            self.register2file(DATABASE_PATH)
                        #añado al user a la lista con los campos necesarios
                        t_expired = time.time() + float(list_palabras[4])
                        recorte = list_palabras[1].split(":")
                        mail = recorte[1]
                        port = recorte[2]
                        self.wfile.write("SIP/2.0 200 OK\r\n\r\n")
                        list_atrib = [self.client_address[0], t_expired, port]
                        #guardo usuario en el diccionario de registro
                        self.dic_reg[mail] = list_atrib
                        #registro en la base de datos
                        self.register2file(DATABASE_PATH)
                        #compruebo si el campos EXPIRES es 0 y actualizo
                        if int(list_palabras[4]) == 0:
                            del self.dic_reg[mail]
                            self.register2file(DATABASE_PATH)
                        #print self.client_address
                        print line
                    if list_palabras[0] == "INVITE":
                    
                        print ' inviteeeeeeeeeeeeeeeeeeeee'
                        recorte = list_palabras[1].split(":")
                        mail = recorte[1]
                        if self.dic_reg:
                            for user in self.dic_reg.keys():
                                if user == mail:
                                    ip_user = self.dic_reg[mail][0]
                                    port_user = int(self.dic_reg[mail][2])
                                    #envio del mensaje
                                    self.send_mensaje(ip_user, port_user, line)
                               
#self.wfile.write("SIP/2.0 404 User Not Found\r\n\r\n")

                    if list_palabras[0] == "ACK":
                        print "ackkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk"
                        recorte = list_palabras[1].split(":")
                        mail = recorte[1]
                        if self.dic_reg:
                            for user in self.dic_reg.keys():
                                if user == mail:
                                    ip_user = self.dic_reg[mail][0]
                                    port_user = int(self.dic_reg[mail][2])
                                    #envio del mensaje
                                    self.send_mensaje(ip_user, port_user, line)
               
                    if list_palabras[0] not in LIST_METODO:
                        excepcion = "SIP/2.0 405 Method Not Allowed\r\n\r\n"
                        self.wfile.write(excepcion)
                else:
                    self.wfile.write("SIP/2.0 400 Bad Request\r\n\r\n")
            break

if __name__ == "__main__":

    #Comprobación de posibles excepciones
    if len(sys.argv) != 2:
        print 'Usage: python proxy_registrar.py config'
        raise SystemExit
    
    FICHERO = str(sys.argv[1])
    
    parser = make_parser()
    chandler = XMLHandler()
    parser.setContentHandler(chandler)
    parser.parse(open(FICHERO))
    DATABASE_PATH = str(chandler.dic_etiq['database_path'])
    SERV_NAME = chandler.dic_etiq['server_name']
    SERV_PORT = int(chandler.dic_etiq['server_puerto'])

    serv = SocketServer.UDPServer(("", SERV_PORT), SIPRegisterHandler)
    print "Server " + SERV_NAME + " listening at port " + str(SERV_PORT) + "..."
    serv.serve_forever()

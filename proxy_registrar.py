#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# PRÁCTICA Final --- JAVIER MARTÍNEZ MOLINA

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import SocketServer
import sys
import time
import uaclient


class XMLHandler(ContentHandler):
    

    def __init__(self):   

        self.etiquetas = {'server': ['name', 'ip', 'puerto'],
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
    """
    Clase de un servidor SIP register
    """

    dic_reg = {} 

    def register2file(self, DATABASE_PATH):
        """
        Cada vez que un user agent se registre o se dé de baja,
        se imprime en el fich una linea con los campos indicados
        y en sucesivas líneas los valores de cada user registrado.
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
        Se comprueba que el tipo de mensaje es un REGISTER,
        la caducidad de los users agent, se añade al dic a los user
        que cumplen las condiciones y se borra a los user con EXPIRES a 0.
        """
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            if line != "":
                list_palabras = line.split()
                print list_palabras
                if list_palabras[0] == "REGISTER":
                    #Compruebo mi dic para localizar posibles users EXPIRES
                    if self.dic_reg:
                        tiempo_actual = time.time()
                        for user in self.dic_reg.keys():
                            if self.dic_reg[user][1] <= tiempo_actual:
                                del self.dic_reg[user]
                        self.register2file()
                    #añado al user a la lista
                    time_expired = time.time() + float(list_palabras[4])
                    recorte = list_palabras[1].split(":")
                    print recorte
                    mail = recorte[1]
                    port = recorte[2]
                    self.wfile.write("SIP/2.0 200 OK\r\n\r\n")
                    list_atrib = [self.client_address[0], time_expired, port]
                    print 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
                    print list_atrib
                    print 'xxxxxxxxxxxxxxxxxxxxxxxxxxxx'
                    self.dic_reg[mail] = list_atrib
                    self.register2file(DATABASE_PATH)
                    print self.dic_reg
                    #compruebo si el campos EXPIRES es 0
                    if int(list_palabras[4]) == 0:
                        del self.dic_reg[mail]
                        self.register2file()
                    #print self.client_address
                    print line
                if list_palabras[0] == "INVITE":
                    print 'hola'
                else:
                    self.wfile.write("SIP/2.0 400 Bad Request\r\n\r\n")
            if not line:
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

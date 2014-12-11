#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# Práctica Final   JAVIER MARTINEZ MOLINA

from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class XMLHandler(ContentHandler):

    def __init__(self):
        self.etiquetas = {'account': ['username', 'passwd'],
            'uaserver': ['ip', 'puerto'],
            'rtpaudio': ['puerto'],
            'regproxy': ['ip', 'puerto'],
            'log': ['path'],
            'audio': ['path']}
            
        self.list_etiquetas = []

    def startElement(self, name, attrs):
        dic = {}
        if name in self.etiquetas:
            dic["name"] = name
            for atributo in self.etiquetas[name]:
                dic[atributo] = attrs.get(atributo, "")
            self.list_etiquetas.append(dic)

    def get_tags(self):
        return self.list_etiquetas

    def __str__(self):
        salida = ""
        for dic in self.list_etiquetas:
            salida += dic["name"] + "\t"
            for etiqueta in dic:
                if dic["name"] != dic[etiqueta] and dic[etiqueta] != "":
                    salida += etiqueta + "=" + '"' + dic[etiqueta] + '"' + "\t"
            salida += "\n"
        return salida

    def extraer_valores(self):
        for dic in self.list_etiquetas:
            for etiqueta in dic:
                if dic["name"] == 'account':
                        if etiqueta == "username":
                            USERNAME = dic[etiqueta]
                            print USERNAME
                        if etiqueta == "passwd":
                            PASSWD = dic[etiqueta]
                            print PASSWD
                if dic["name"] == 'uaserver':
                        if etiqueta == "ip":
                            IP_UASERVER = dic[etiqueta]
                            print IP_UASERVER
                        if etiqueta == "puerto":
                            PORT_UASERVER = dic[etiqueta]
                            print PORT_UASERVER
                if dic["name"] == 'rtpaudio':
                        if etiqueta == "puerto":
                            PORT_RTPAUDIO = dic[etiqueta]
                            print PORT_RTPAUDIO
                if dic["name"] == 'regproxy':
                        if etiqueta == "ip":
                            IP_PROXY = dic[etiqueta]
                            print IP_PROXY
                        if etiqueta == "puerto":
                            PORT_PROXY = dic[etiqueta]
                            print PORT_PROXY
                if dic["name"] == 'log':
                        if etiqueta == "path":
                            LOG_PATH = dic[etiqueta]
                            print LOG_PATH
                if dic["name"] == 'audio':
                        if etiqueta == "path":
                            AUDIO_PATH = dic[etiqueta]
                            print AUDIO_PATH
                   
                        

if __name__ == "__main__":

    parser = make_parser()
    chandler = XMLHandler()
    parser.setContentHandler(chandler)
    parser.parse(open('ua1.xml'))
    print chandler.get_tags()
    chandler.extraer_valores()

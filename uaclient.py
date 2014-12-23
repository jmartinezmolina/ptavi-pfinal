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
                            self.dic_etiq['account_username'] = dic[etiqueta]
                            print self.dic_etiq['account_username']
                        if etiqueta == "passwd":
                            self.dic_etiq['account_passwd'] = dic[etiqueta]
                            print self.dic_etiq['account_passwd']
                if dic["name"] == 'uaserver':
                        if etiqueta == "ip":
                            self.dic_etiq['uaserver_ip'] = dic[etiqueta]
                            print self.dic_etiq['uaserver_ip']
                        if etiqueta == "puerto":
                            self.dic_etiq['uaserver_puerto'] = dic[etiqueta]
                            print self.dic_etiq['uaserver_puerto']
                if dic["name"] == 'rtpaudio':
                        if etiqueta == "puerto":
                            self.dic_etiq['rtpaudio_puerto'] = dic[etiqueta]
                            print self.dic_etiq['rtpaudio_puerto']
                if dic["name"] == 'regproxy':
                        if etiqueta == "ip":
                            self.dic_etiq['regproxy_ip'] = dic[etiqueta]
                            print self.dic_etiq['regproxy_ip']
                        if etiqueta == "puerto":
                            self.dic_etiq['regproxy_puerto'] = dic[etiqueta]
                            print self.dic_etiq['regproxy_puerto']
                if dic["name"] == 'log':
                        if etiqueta == "path":
                            self.dic_etiq['log_path'] = dic[etiqueta]
                            print self.dic_etiq['log_path']
                if dic["name"] == 'audio':
                        if etiqueta == "path":
                            self.dic_etiq['audio_path'] = dic[etiqueta]
                            print self.dic_etiq['audio_path']
                   
                        

if __name__ == "__main__":

    parser = make_parser()
    chandler = XMLHandler()
    print chandler.dic_etiq
    parser.setContentHandler(chandler)
    parser.parse(open('ua1.xml'))
    #print chandler.get_tags()
    chandler.extraer_valores()
    print chandler.dic_etiq

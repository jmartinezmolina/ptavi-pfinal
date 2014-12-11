#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# Práctica Final   JAVIER MARTINEZ MOLINA

from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class XMLHandler(ContentHandler):

    def __init__(self):
        self.etiquetas = {
            'account': ['username', 'passwd'],
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

    def do_local(self):
        for dic in self.list_etiquetas:
            for etiqueta in dic:
                if etiqueta == "username":
                    recurso = dic[etiqueta]
                    print recurso
                    #os.system("wget -q " + recurso)
                    #elem_div = recurso.split('/')
                    #dic[etiqueta] = elem_div[-1]


if __name__ == "__main__":

    parser = make_parser()
    chandler = XMLHandler()
    parser.setContentHandler(chandler)
    parser.parse(open('ua1.xml'))
    print chandler.get_tags()
    chandler.do_local()

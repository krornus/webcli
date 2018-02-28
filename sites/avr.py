import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

import requests
import shlex
import lxml.etree as etree

from browser import *
import engine

def new(visit):
    return AVR(visit=visit)

class AVR(SwappableCmd):

    def __init__(self,visit=None):
        self.name = "avr"
        self.url = "https://www.microchip.com/webdoc/avrassembler/avrassembler.wb_{}.html"

        self.valid_re = self.domain("microchip.com/webdoc/avrassembler")

        self.get_instance=visit

        self.abbrev = True

        self.page = None
        self.instruction = None

        SwappableCmd.__init__(self)
        self.set_prompt(self.name)

    def valid_url(self, url):
        return bool(self.valid_re.match(url))

    def do_visit(self, url):

        url = self.split_positionals(url, "visit")

        if len(url) == 0:
            writeln("usage: visit <url>")
            return

        url = url[0]

        if not self.valid_url(url):
            writeln("invalid url: '{}'".format(url))
            return


        self.page = engine.Page(url, load=True)
        self.lpr(self.page)

    def do_query(self, args, opt=None):

        args = self.split_positionals(args, ["query","search"])
        print "loading",self.url.format(args[0].upper())

        self.page = engine.Page(self.url.format(args[0].upper(), load=True))
        self.lpr(self.page)

    do_search = do_query

    def lpr(self, page):
        self.load_results(page)
        self.print_results()

    def load_results(self, page):

        xsection = engine.Path('//div[@class="section"]',link=False)
        results = engine.search(page, xsection)

        if len(results) != 1:
            return

        self.instruction = etree.tostring(results[0],method="text",encoding="UTF-8")


    def print_results(self):
        print self.instruction

    def split_positionals(self,args,cmds):

        if not isinstance(cmds,list):
            cmds = [cmds]

        args = shlex.split(args)
        if len(args) > 1 and any(args[0] in x for x in cmds):
            args = args[1:]
        else:
            args = args[0:]

        return args

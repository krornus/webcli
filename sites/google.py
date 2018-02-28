import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

import requests
import shlex

from browser import *
import engine

def new(visit):
    return Google(visit=visit)

class Google(SwappableCmd):

    def __init__(self,visit=None):
        self.name = "google"
        self.url = "https://www.google.com/search"

        self.valid_re = self.domain("google.com")

        self.get_instance=visit

        self.abbrev = True

        self.page = None
        self.titles = []
        self.links = []

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

        self.page = engine.Page(self.url, params={"q":args[0]}, load=True)
        self.lpr(self.page)

    do_search = do_query

    def lpr(self, page):
        self.load_results(page)
        self.print_results()

    def load_results(self, page):

        xtitle = engine.Path('//h3[@class="r"]/a/text()',link=False)
        xlink = engine.Path('//h3[@class="r"]/a/@href')
        results = engine.search(page, [xtitle,xlink])

        self.titles = []
        self.links = []

        for t,l in zip(results[0], results[1]):
            self.titles.append(t)
            self.links.append(l)

    def print_results(self):
        for i,t in enumerate(self.titles):
            writeln("{}: {}".format(i+1,t))
            writeln("  {}".format(self.links[i]))

    def do_next(self, args):

        if not self.page:
            writeln("[-] no results loaded!")
            return
        xpath = engine.Path('//a[@id="pnnext"]/@href')
        n = engine.search(self.page, xpath)

        if not n:
            writeln("[-] no more results!")
            return

        self.page = engine.Page(n[0], load=True)
        self.lpr(self.page)

    def do_previous(self, args):

        if not self.page:
            writeln("[-] no results loaded!")
            return

        xpath = engine.Path('//a[@id="pnprev"]/@href')
        n = engine.search(self.page, xpath)

        if not n:
            writeln("[-] no more results!")
            return

        self.page = engine.Page(n[0], load=True)
        self.lpr(self.page)

    def do_open(self, args):

        args = self.split_positionals(args, "open")
        options = []

        if len(args) > 1:
            options = args[1:]

        n = -1
        try:
            n = int(args[0],0)-1
        except:
            return

        if n not in range(0,len(self.links)):
            print "[-] invalid selection"
            return

        url = self.links[n]

        instance = None
        if self.get_instance:
            instance = self.get_instance(url)

        if instance:
            self.swap(instance,url)
        else:
            engine.open_url(url,options=options)

    def split_positionals(self,args,cmds):

        if not isinstance(cmds,list):
            cmds = [cmds]

        args = shlex.split(args)
        if len(args) > 1 and any(args[0] in x for x in cmds):
            args = args[1:]
        else:
            args = args[0:]

        return args

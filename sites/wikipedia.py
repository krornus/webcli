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
    return Wikipedia(visit=visit)

class Wikipedia(SwappableCmd):

    def __init__(self,visit=None):

        self.name = "wikipedia"

        self.base_url = "https://en.wikipedia.org"
        self.search_url = self.base_url+"/w/index.php"

        self.abbrev = True

        self.wiki = self.domain("en.wikipedia.org/wiki/.+",www=False)
        self.search = self.domain("en.wikipedia.org/w/index.php\?.+",www=False)

        self.header = re.compile("^h[0-9]+")

        self.valid_url = self.valid_wiki

        self.get_instance=visit
        self.results = []
        self.page = None

        SwappableCmd.__init__(self)
        self.set_prompt(self.name)

    def valid_wiki(self, url):
        if isinstance(url,str):
            return bool(self.wiki.match(url))
        else:
            return False

    def valid_search(self, url):
        if isinstance(url,str):
            return bool(self.search.match(url))
        else:
            return False

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

        self.page = engine.Page(
            self.search_url,
            params={"search":args[0],"fulltext":1},
            load=True
        )

        self.lpr(self.page)

    do_search = do_query

    def lpr(self, page):
        self.load_results(page)
        self.print_results()

    def load_results(self, page):

        if self.valid_wiki(page.url):
            self.load_wiki(page)
        if self.valid_search(page.url):
            self.load_search(page)

    def load_wiki(self, page):

        if not self.valid_wiki(page.url):
            return

        pwiki = '//div[@class="mw-parser-output"]/*'
        xwiki = engine.Path(pwiki,link=False)

        results = engine.search(page, [xwiki])

        if len(results) == 0:
            return

        rwiki = results[0]
        wiki = ""

        for child in rwiki:
            if self.header.match(child.tag):
                wiki+="\n"
                wiki+="-"*80
                wiki+="\n"
                wiki+=etree.tostring(child,method="text",encoding="UTF-8")
                wiki+="-"*80
                wiki+="\n"
            if child.tag.decode("ascii","ignore") == "p":
                wiki+=etree.tostring(child,method="text",encoding="UTF-8")

        self.wiki = wiki

    def load_search(self, page):

        if not self.valid_search(page.url):
            return

        presult = '//div[@class="mw-search-result-heading"]/a'
        xresult = engine.Path(presult,link=False)

        results = engine.search(page, xresult)

        for result in results:
            print "UNIMPLEMENTED, ADD SUBTREE TO ENGINE"
            print result.attrib['href'],result.attrib['title']

    def print_results(self):
        print self.wiki

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


        print args.parsed.dump()
        if not isinstance(self.results,Questions):
            print "[-] not in query"
            return

        args = self.split_positionals(args, "open")
        options = []

        if len(args) > 1:
            options = args[1:]

        n = -1
        try:
            n = int(args[0],0)-1
        except:
            return

        if n not in range(0,len(self.results.questions)):
            print "[-] invalid selection"
            return

        url = self.results.questions[n].link
        instance = self.get_instance(url)

        if instance == self:
            instance.do_visit(url)
        elif instance:
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

import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

import requests
import shlex
import lxml.etree as etree

from browser import *
import engine

class Question:
    def __init__(self,title,link):
        self.title = title
        self.link = link

class Questions:
    def __init__(self,query,questions):
        self.questions = questions
        self.query = query

class Answers:
    def __init__(self,question,accepted,answers):
        self.question = question
        self.answers = answers
        self.accepted = accepted

def new(visit):
    return StackOverflow(visit=visit)

class StackOverflow(SwappableCmd):

    def __init__(self,visit=None):
        self.name = "stackoverflow"

        self.search_url = "https://stackoverflow.com/search"

        self.abbrev = True

        self.question = self.domain("stackoverflow.com/questions/[0-9]+",www=False)
        self.search = self.domain("stackoverflow.com/search?",www=False)

        self.valid_url = self.valid_question

        self.get_instance=visit

        self.results = []

        self.page = None
        self.titles = []
        self.links = []

        SwappableCmd.__init__(self)
        self.set_prompt(self.name)

    def valid_question(self, url):
        if isinstance(url,str):
            return bool(self.question.match(url))
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

        self.results = Questions(args[0],[])

        self.page = engine.Page(self.search_url, params={"q":args[0]}, load=True)
        self.lpr(self.page)

    do_search = do_query

    def lpr(self, page):
        self.load_results(page)
        self.print_results()

    def load_results(self, page):

        if self.valid_question(page.url):
            self.load_answers(page)
        if self.valid_search(page.url):
            self.load_questions(page)

    def do_accepted(self, args):
        if not isinstance(self.results, Answers):
            writeln("[-] no question selected")
            return
        writeln(self.results.accepted)

    def do_answers(self, args):
        if not isinstance(self.results, Answers):
            writeln("[-] no question selected")
            return

        for answer in self.results.answers:
            writeln(answer.strip())
            writeln("")
            writeln("-"*80)
            writeln("")

    def load_answers(self, page):

        if not self.valid_url(page.url):
            return

        paccepted='//div[@class="answer accepted-answer"]'
        panswers='//div[@class="answer"]'
        panswer='/table/tr/td[@class="answercell"]/div[@class="post-text"]'

        xaccepted = engine.Path(paccepted+panswer,link=False)
        xanswers = engine.Path(panswers+panswer,link=False)

        results = engine.search(page, [xaccepted,xanswers])

        self.results = None

        raccepted = results[0]
        ranswers = results[1]

        answers = []
        accepted = None

        if len(raccepted) > 0:
            accepted = etree.tostring(raccepted[0],method="text",encoding="UTF-8")
        for answer in ranswers:
            answers.append(etree.tostring(answer,method="text",encoding="UTF-8"))

        self.results = Answers("unimplemented", accepted, answers)

    def load_questions(self, page):

        if not self.valid_search(page.url):
            return

        psummary='//div[@class="summary"]/div[@class="result-link"]'
        xsummary = engine.Path(psummary,link=False)

        plink="./span/a/@href"
        ptitle="./span/a/text()"

        ptext="./span"

        xtitle = engine.Path(ptitle,link=False)
        xlink = engine.Path(plink,link=True)

        results = engine.search(page, xsummary)

        if len(results) == 0:
            writeln("[-] no results found")
            return

        if not isinstance(self.results, Questions):
            self.results = Questions("ERR",[])

        for summary in results:
            page = engine.Page(page.url, tree=summary)

            link = engine.search(page, xlink)
            title = engine.search(page, xtitle)

            if len(link) == 0 or len(title) == 0:
                continue

            link = link[0].strip()
            title = title[0].strip()[3:]

            self.results.questions.append(Question(title,link))

    def print_results(self):
        if isinstance(self.results,Questions):
            writeln("\nQUERY: {}\n".format(self.results.query))
            for i,question in enumerate(self.results.questions):
                writeln("{}: {}".format(i+1,question.title))
        elif isinstance(self.results,Answers):
            writeln(self.results.accepted)

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

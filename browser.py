import sys
from cmd2 import Cmd, make_option, options, set_use_arg_list
import re

def write(s):
    s=str(s)
    sys.stdout.write(s)

def writeln(s):
    s=str(s)
    sys.stdout.write(s+"\n")

class SwappableCmd(Cmd):
    def __init__(self):
        self.lprompt = "("
        self.rprompt = ") -> "
        self.priority = 0
        Cmd.__init__(self)

    def set_prompt(self, site):
        self.prompt = self.lprompt + site + self.rprompt

    def domain(self, d, www=True):

        pre = ""
        if www:
            pre = "www\."

        return re.compile("^(?:(?:https?://){})?{}(?:/.*)?$".format(pre,d))

    def run(self,args=""):
        self.cmdloop()

    def swap(self, instance, args=""):
        if args:
            instance.do_visit(args)
        instance.run("")

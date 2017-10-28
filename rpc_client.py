#coding:utf-8
import xmlrpc.client

proxy = xmlrpc.client.ServerProxy('http://127.0.0.1:8003')
s = proxy.add(1, 2)
print(s)
s = proxy.sub(5, 3)
print(s)

import cmd
import os

class CLI(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = ">>\t"
        self.proxy = xmlrpc.client.ServerProxy("http://127.0.0.1:8003")

    def do_status(self, arg):
        print("do_status:", arg)
        print(self.proxy.status())

    def help_status(self):
        print("do_status help")

    def do_stop(self, arg):
        arg_list = arg.split(" ")
        if "all" in arg_list:
            print(self.proxy.stop_all())

    def help_stop(self):
        print("stop all")

    def do_start(self, arg):
        arg_list = arg.split(" ")
        if "all" in arg_list:
            print(self.proxy.start_all())

    def help_start(self):
        print("start all")

    def do_startone(self, arg):
        print(self.proxy.start_one(arg))

    def help_startone(self):
        print("startone spwn1")

    def do_stopone(self, arg):
        print(self.proxy.stop_one(arg))

    def help_stopone(self):
        print("stopone spwn1")

    def do_exit(self, arg):
        print(self.proxy.exit())
        os._exit(127)

    def help_exit(self):
        print("exit")

    def do_quit(self):
        return True

    def help_quit(self):
        print("quit")

if __name__ == '__main__':
    c = CLI()
    c.cmdloop()



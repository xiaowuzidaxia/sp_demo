#coding:utf-8
import os
import time
import sys
import signal
import threading
import selectors

from fcntl import fcntl
from fcntl import F_SETFL, F_GETFL
import select

from share_program.supervisor_test.sp_demo.rpc_server import ForkXMLRPCServer

source = 10


class RunObj(object):

    def run(self):
        while True:
            pid = os.getpid()
            print(pid)
            with open("sub_"+str(pid)+".txt", "a") as f:
                f.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+" sub pid \n")
                print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+ " " + str(pid) +" sub pid \n")
            time.sleep(2)


def make_pipes():
    """ Create pipes for parent to child stdin/stdout/stderr
    communications.  Open fd in nonblocking mode so we can read them
    in the mainloop without blocking """
    pipes = {}
    try:
        pipes['child_stdin'], pipes['stdin'] = os.pipe()
        pipes['stdout'], pipes['child_stdout'] = os.pipe()
        pipes['stderr'], pipes['child_stderr'] = os.pipe()
        for fd in (pipes['stdout'], pipes['stderr'], pipes['stdin']):
            fcntl(fd, F_SETFL, fcntl(fd, F_GETFL) | os.O_NDELAY)
        return pipes
    except OSError:
        raise

def close_fd(fd):
    os.close(fd)

def daemonize():
    print("fork")
    pid = os.fork()

    if pid:
        print("this parent process")
        sys.exit(0)
    else:
        print("sub process")
        os.chdir(".")
        os.setsid()
        os.umask(0)
        fd = open("/dev/null", "a+")
        os.dup2(fd.fileno(), 0)
        os.dup2(fd.fileno(), 1)
        os.dup2(fd.fileno(), 2)
        fd.close()

SUB_RUNNING = 1
SUB_STOP = 0


class SubSpwn(object):
    pid = 0
    status = SUB_STOP

    def __init__(self, name):
        self.name = name

    def dup2(self, frm, to):
        return os.dup2(frm, to)

    def spwn(self):
        self.pipes = make_pipes()

        pid = os.fork()
        if pid:
            self.pid = pid
            self.status = SUB_RUNNING
            print("SubSpwn pid", pid)
            for fdname in ('child_stdin', 'child_stdout', 'child_stderr'):
                close_fd(self.pipes[fdname])
            return pid

        fd = open("/dev/null", "a+")
        os.dup2(fd.fileno(), 0)
        os.dup2(fd.fileno(), 1)
        os.dup2(fd.fileno(), 2)
        # fd.close()
        try:
            self.dup2(self.pipes['child_stdin'], 0)
            self.dup2(self.pipes['child_stdout'], 1)
            self.dup2(self.pipes['child_stderr'], 2)
            r = RunObj()
            r.run()
            # os.setsid()
            # os.execv(sys.executable, [sys.executable, "/Users/wuzi/workpy/worktest/supervisortest/process1.py"])
            print("sss")
        finally:
            os._exit(127)


class Control(ForkXMLRPCServer):
    def __init__(self, *args, **kwargs):
        ForkXMLRPCServer.__init__(self, *args, **kwargs)
        # daemonize()
        self.sub = [SubSpwn("spwn1"), SubSpwn("spwn2")]
        print("sub spwn")
        for sub in self.sub:
            sub.spwn()

    def add_pipes(self, register):
        for sub in self.sub:
            print("sub pipe :", sub.pipes["stdout"])
            register.register(sub.pipes['stdout'], selectors.EVENT_WRITE)

    def read_pipes(self):
        for sub in self.sub:
            try:
                print("stdout :", os.read(sub.pipes["stdout"], 1024))
            except BlockingIOError:
                print("sub stdout error")
            try:
                print("stdout :", os.read(sub.pipes["stderr"], 1024))
            except BlockingIOError:
                print("sub stderr error")

    def check_process(self):
        pid = "pid"
        status = "status"
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
            print("pid: {}, status: {}".format(pid, status))
            if pid != 0:
                with open("control.txt", "a") as f:
                    f.write("pid: {}, status: {}".format(pid, status) + "\n")
            for sub in self.sub:
                if sub.pid == pid and sub.status == SUB_RUNNING:
                    sub.spwn()
        except os.error:
            print("os error:", os.error)
            with open("control3.txt", "a") as f:
                f.write("pid: {}, status: {}".format(pid, status) + "\n")

        self.read_pipes()

    def start_all(self):
        res = []
        for sub in self.sub:
            if sub.status == SUB_STOP:
                sub.spwn()
                res.append(sub.name + "already start")
            else:
                res.append(sub.name + ":" + str(sub.pid) + "already start")
        return "\n".join(res)

    def start_one(self, name):
        res = " no sub "
        for sub in self.sub:
            if name == sub.name and sub.status == SUB_STOP:
                sub.spwn()
                res = sub.name + ":" + str(sub.pid) + "-- now start"
                return res
        return res

    def stop_all(self):
        res = []
        for sub in self.sub:
            sub.status = SUB_STOP
            os.kill(sub.pid, signal.SIGINT)
            res.append(sub.name + "already stop")
        return "\n".join(res)

    def stop_one(self, name):
        for sub in self.sub:
            if name == sub.name and sub.status == SUB_RUNNING:
                sub.status = SUB_STOP
                os.kill(sub.pid, signal.SIGINT)
                res = sub.name + ": stop ****"
                return res
        res = "none sub stop or sub name"
        return res

    def status(self):
        res = []
        for sub in self.sub:
            res.append(sub.name + ":" + str(sub.status))
        return "\n".join(res)

    def exit(self):
        pid = os.getpid()
        for sub in self.sub:
            if sub.status == SUB_RUNNING:
                sub.status = SUB_STOP
                os.kill(sub.pid, signal.SIGINT)
        # os.kill(pid, signal.SIGKILL)
        t = threading.Thread(target=kill_self, args=(pid, ))
        t.start()
        return "exit ok:" + str(pid)


def kill_self(pid):
    time.sleep(3)
    os.kill(pid, signal.SIGKILL)

if __name__ == '__main__':
    server = Control(("127.0.0.1", 8003))
    import asyncore
    import asynchat
    def add(x, y):
        return x+y
    def sub(x, y):
        return x-y
    server.register_multicall_functions()
    server.register_function(add, "add")
    server.register_function(sub, "sub")
    server.register_function(server.status, "status")
    server.register_function(server.stop_all, "stop_all")
    server.register_function(server.start_all, "start_all")
    server.register_function(server.stop_one, "stop_one")
    server.register_function(server.start_one, "start_one")
    server.register_function(server.exit, "exit")
    server.serve_forever()
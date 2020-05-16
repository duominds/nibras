__version__ = "1.0.0"

import yaml
import time
import sys
import socket
import os
import re
import shutil
import datetime
import paramiko
from paramiko.ssh_exception import *
import threading
import concurrent.futures
import logging
from tqdm import trange, tqdm


class SSHParamiko:
    def __init__(
        self,
        host,
        user,
        password,
        port,
        commands,
        secret,
        timeout=2,
        look_for_keys=False,
        allow_agent=False,
        auto_add_keys=True,
        shell_mode=True,
        chunk_size=65535,
    ):
        if host:
            self.host = host
        else:
            raise ValueError("Host must be set")
        self.user = user
        self.password = password
        self.port = int(port)
        self.cmddata = commands
        self.secret = secret
        self.timeout = timeout
        self.look_for_keys = look_for_keys
        self.allow_agent = allow_agent
        self.auto_add_keys = auto_add_keys
        self.shell_mode = shell_mode
        self.chunk_size = chunk_size
        self.output = ""
        self.prompt = "SW"
        self.stdin = self.stdout = self.stderr = self._conn = None
        self.streams = {"in": None, "out": None, "err": None}

    def isOpen(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        try:
            socket.inet_aton(self.host)
            self.sock.connect((self.host, self.port))
            self.sock.shutdown(socket.SHUT_RDWR)
            return True
        except OSError as e:
            self.output = "Error 100: Host Un Reachanble"
            return False
        except:
            return False

    def checkHost(self, retry=3, delay=1):
        ipup = False
        for i in range(int(retry)):
            if self.isOpen():
                ipup = True
                break
            else:
                time.sleep(delay)
        return ipup, self.host, self.port

    def dircheck(self):
        rootabspath = os.path.abspath(".")
        dataabspath = os.path.abspath(os.path.join(rootabspath, "data"))
        dt = datetime.datetime.now().strftime("%Y-%m-%d")
        self.todaydata = os.path.abspath(os.path.join(dataabspath, dt))
        try:
            os.stat(dataabspath)
        except:
            os.mkdir(dataabspath)
        try:
            os.stat(self.todaydata)
        except:
            os.mkdir(self.todaydata)

        if os.listdir(self.todaydata):
            for filename in os.listdir(self.todaydata):
                filepath = os.path.join(self.todaydata, filename)
                try:
                    if os.path.isfile(filepath) or os.path.islink(filepath):
                        os.unlink(filepath)
                    elif os.path.isdir(filepath):
                        shutil.rmtree(filepath)
                except Exception as e:
                    print("Failed to delete %s. Reason: %s" % (filepath, e))
        return self.todaydata

    def sshhost(self):
        self.client = paramiko.SSHClient()
        if self.auto_add_keys:
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(
                hostname=self.host,
                username=self.user,
                password=self.password,
                look_for_keys=self.look_for_keys,
                allow_agent=self.allow_agent,
                timeout=self.timeout,
            )
            return True, self.host
        except AuthenticationException:
            self.output = "Error 200: Failure Authentication"
            return False, self.host

    def check_enable_mode(self):
        """Check if we are in privilege exec. Return boolean"""
        priv_check = "#"
        self.sendtext("\n")
        self.output = self.getcommandresult("\n", self.connection)
        return priv_check in self.output

    def runsshcmdinit(self):
        if self.shell_mode:
            self.connection = self.client.invoke_shell()
            self.connection.setblocking(0)
            self.connection.keep_this = self.client

        if self.shell_mode:
            self.sendtext("terminal length 0\n")
            self.output = self.getcommandresult("disable paging", self.connection)
            if not self.check_enable_mode():
                self.sendtext("enable\n")
                pattern = "password"
                self.output = self.read_until_prompt_or_pattern(pattern)
                if re.search(pattern, self.output, flags=re.IGNORECASE):
                    self.sendtext(self.secret + "\n")

            if self.check_enable_mode():
                return True, self.host
            else:
                self.output = "Error 300: Bad Secret"
                return False, self.host

    def runsshcmd(self):
        self.sendtext("\n")
        self.output = self.getcommandresult("\n", self.connection)
        self.prompt = self.output.split()[-1][:-1]
        self.output = ""
        for cmd in self.cmddata:
            if self.shell_mode:
                self.sendtext(cmd + "\n")
                self.output += self.getcommandresult(cmd, self.connection)
            else:
                (
                    self.streams["in"],
                    self.streams["out"],
                    self.streams["err"],
                ) = self.client.exec_command(cmd + "\n")
                while not self.streams["out"].channel.exit_status_ready():
                    while self.streams["out"].channel.recv_ready():
                        self.output += (
                            self.streams["out"]
                            .channel.recv(self.chunk_size)
                            .decode("ascii")
                        )
        self.outputwriter()
        self.sshclose()

    def outputwriter(self):
        cmdfile = os.path.join(self.todaydata, self.host + "-" + self.prompt + ".txt")
        with open(cmdfile, "w") as outfile:
            outfile.write(self.output)

    def sendtext(self, text):
        if self.shell_mode:
            try:
                self.connection.send(text)
            except AttributeError:
                raise ("Attempting to use a session that was not opened")
        else:
            self.client.exec_command(text)

    def getcommandresult(self, cmd, connection):
        interval = 0.1
        maxseconds = 10
        maxcount = maxseconds / interval
        input_idx = 0
        timeoutflag = False
        starttime = datetime.datetime.now()
        startsecs = time.mktime(starttime.timetuple())
        self.output = ""
        while True:
            if self.connection.recv_ready():
                data = self.connection.recv(self.chunk_size).decode("ascii")
                self.output += data

            if self.connection.exit_status_ready():
                break

            nowtime = datetime.datetime.now()
            nowsecs = time.mktime(nowtime.timetuple())
            estime = nowsecs - startsecs
            if estime > maxseconds:
                timeoutflag = True
                break

            rbuffer = self.output.rstrip(" ")
            if len(rbuffer) > 0 and (rbuffer[-1] == "#" or rbuffer[-1] == ">"):
                break
            time.sleep(0.2)

        if self.connection.recv_ready():
            data = self.connection.recv(self.chunk_size).decode("ascii")
            self.output += data
        return self.output

    def read_until_prompt_or_pattern(self, pattern=""):
        maxseconds = 2
        starttime = datetime.datetime.now()
        startsecs = time.mktime(starttime.timetuple())
        timeoutflag = False
        self.output = ""
        while True:
            if self.connection.recv_ready():
                data = self.connection.recv(self.chunk_size).decode("ascii")
                self.output += data
            if self.connection.exit_status_ready():
                break
            nowtime = datetime.datetime.now()
            nowsecs = time.mktime(nowtime.timetuple())
            estime = nowsecs - startsecs
            if estime > maxseconds:
                timeoutflag = True
                break
            if re.search(pattern, self.output, flags=re.IGNORECASE):
                break
            time.sleep(0.2)
        if self.connection.recv_ready():
            data = self.connection.recv(self.chunk_size).decode("ascii")
            self.output += data
        return self.output

    def sshclose(self):
        self.client.close()

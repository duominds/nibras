__version__ = "1.0.0"

import os
import shutil
from datetime import datetime
from tqdm import tqdm
from lib import *
from lib.InputParser import *
from lib.SSHParamiko import *
from lib.Parser import *


def dirinit():
    rootabspath = os.path.abspath(".")
    outputabspath = os.path.abspath(os.path.join(rootabspath, "output"))
    """output/ Directory init"""
    if os.listdir(outputabspath):
        for filename in os.listdir(outputabspath):
            filepath = os.path.join(outputabspath, filename)
            try:
                if os.path.isfile(filepath) or os.path.islink(filepath):
                    os.unlink(filepath)
                elif os.path.isdir(filepath):
                    shutil.rmtree(filepath)
            except Exception as e:
                print("Failed to delete %s. Reason: %s" % (filepath, e))
    return outputabspath


def dirend():
    rootabspath = os.path.abspath(".")
    configabspath = os.path.abspath(os.path.join(rootabspath, "config"))
    inputabspath = os.path.abspath(os.path.join(rootabspath, "input"))
    newinputfileheader = datetime.now().strftime("-%Y-%m-%d-%H_%M")
    dataabspath = os.path.abspath(os.path.join(rootabspath, "data"))
    dt = datetime.now().strftime("%Y-%m-%d")
    todaydata = os.path.abspath(os.path.join(dataabspath, dt))
    """config/ Directory ending"""
    try:
        os.stat(configabspath)
    except:
        os.mkdir(configabspath)
        print(
            u"\u001b[31;1mExit Code File switch_cmd.yaml Not Found In config Directory!\u001b[0m"
        )
        sys.exit()
    if (
        "switch_cmd.yaml" in os.listdir(configabspath)
        and len(os.listdir(configabspath)) > 1
    ):
        for filename in os.listdir(configabspath):
            if filename != "switch_cmd.yaml":
                filepath = os.path.join(configabspath, filename)
                try:
                    if os.path.isfile(filepath) or os.path.islink(filepath):
                        os.unlink(filepath)
                    elif os.path.isdir(filepath):
                        shutil.rmtree(filepath)
                except Exception as e:
                    print("Failed to delete %s. Reason: %s" % (filepath, e))
    else:
        print(
            u"\u001b[31;1mExit Code File switch_cmd.yaml Not Found In config Directory!\u001b[0m"
        )
        sys.exit()
    """input/ Directory ending"""
    inputfiles = [
        filename
        for filename in os.listdir(inputabspath)
        if filename.startswith("input")
    ]
    for filename in inputfiles:
        newfilename = ".".join(
            [filename.split(".")[0] + newinputfileheader] + filename.split(".")[1:]
        )
        try:
            shutil.move(
                os.path.join(inputabspath, filename),
                os.path.join(inputabspath, newfilename),
            )
        except:
            print("Error: Couldn't Rename input files")
    """data/ Directory ending"""
    if os.listdir(dataabspath):
        for filename in os.listdir(dataabspath):
            filepath = os.path.join(dataabspath, filename)
            try:
                if os.path.isfile(filepath) or os.path.islink(filepath):
                    os.unlink(filepath)
                elif os.path.isdir(filepath):
                    shutil.rmtree(filepath)
            except Exception as e:
                print("Failed to delete %s. Reason: %s" % (filepath, e))
        shutil.rmtree(dataabspath)


def run():
    start = time.time()
    with open("config/results.yaml") as hosts_file:
        hostsdata = yaml.load(hosts_file, Loader=yaml.FullLoader)

    with open("config/switch_cmd.yaml") as cmd_file:
        cmddata = yaml.load(cmd_file, Loader=yaml.FullLoader)
    hosts = hostsdata.keys()
    downhostsConnections = {}
    SSHParamikoConnectionsdict = {}
    AuthConnectionsdict = {}
    FailAuthConnectionsdict = {}
    PrivConnections = {}
    FailPrivConnections = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(hosts)) as executor1:
        connections = {
            executor1.submit(
                SSHParamiko,
                host,
                hostsdata[host]["user"],
                hostsdata[host]["password"],
                hostsdata[host]["port"],
                cmddata,
                hostsdata[host]["secret"],
                shell_mode=True,
            ): host
            for host in hosts
        }
        for future in concurrent.futures.as_completed(connections):
            SSHParamikoConnectionsdict[future.result().host] = future.result()
            todaydata = future.result().dircheck()
    SSHParamikoConnections = SSHParamikoConnectionsdict.values()
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(SSHParamikoConnections)
    ) as executor2:
        checkHostList = executor2.map(SSHParamiko.checkHost, SSHParamikoConnections)
        for hostStatus in checkHostList:
            if hostStatus[0]:
                pass
            else:
                downhostsConnections[hostStatus[1]] = SSHParamikoConnectionsdict[
                    hostStatus[1]
                ]
    if downhostsConnections:
        for ip in downhostsConnections:
            del SSHParamikoConnectionsdict[ip]
    if len(SSHParamikoConnectionsdict) == 0:
        print(u"\u001b[31;1mExit Code All Remaining Hosts Un Reachable!\u001b[0m")
        sys.exit()
    if downhostsConnections and SSHParamikoConnectionsdict:
        run = input(
            "Are you want to proceed running Nibras and ignore down hosts? [Y/N] "
        )
        if run.lower().startswith("y"):
            """Write Error 100: Host Un Reachanble in Multithreading"""
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=len(downhostsConnections)
            ) as executor3:
                down_conn = executor3.map(
                    SSHParamiko.outputwriter, downhostsConnections.values()
                )
        else:
            exetime = time.time() - start
            sys.exit()
    if SSHParamikoConnectionsdict:
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(SSHParamikoConnectionsdict)
        ) as executor4:
            AuthCheckHostList = executor4.map(
                SSHParamiko.sshhost, SSHParamikoConnectionsdict.values()
            )
            for AuthHost in AuthCheckHostList:
                if not AuthHost[0]:
                    FailAuthConnectionsdict[AuthHost[1]] = SSHParamikoConnectionsdict[
                        AuthHost[1]
                    ]
                else:
                    AuthConnectionsdict[AuthHost[1]] = SSHParamikoConnectionsdict[
                        AuthHost[1]
                    ]
            if len(FailAuthConnectionsdict) == len(SSHParamikoConnectionsdict):
                print(
                    u"\u001b[31;1mExit Code All Remaining Hosts Failed to Authenticate!\u001b[0m"
                )
                exetime = time.time() - start
                sys.exit()
            elif len(FailAuthConnectionsdict) > 0:
                """Write Error 200: Failure Authentication in Multithreading"""
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=len(FailAuthConnectionsdict)
                ) as executor5:
                    failAuth = executor5.map(
                        SSHParamiko.outputwriter, FailAuthConnectionsdict.values()
                    )
    if AuthConnectionsdict:
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(AuthConnectionsdict)
        ) as executor6:
            PrivCheckHostList = executor6.map(
                SSHParamiko.runsshcmdinit, AuthConnectionsdict.values()
            )
            for privHost in PrivCheckHostList:
                if not privHost[0]:
                    FailPrivConnections[privHost[1]] = AuthConnectionsdict[privHost[1]]
                else:
                    PrivConnections[privHost[1]] = AuthConnectionsdict[privHost[1]]
            if len(FailPrivConnections) == len(AuthConnectionsdict):
                print(
                    u"\u001b[31;1mExit Code All Remaining Hosts Failed to Enter Privilege Mode!\u001b[0m"
                )
                exetime = time.time() - start
                sys.exit()
            elif len(FailPrivConnections) > 0:
                """Write Error 300: Bad Secret in Multithreading"""
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=len(FailPrivConnections)
                ) as executor7:
                    failAuth = executor7.map(
                        SSHParamiko.outputwriter, FailPrivConnections.values()
                    )
    if PrivConnections:
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(PrivConnections)
        ) as executor8:
            PrivCheckHostList = list(
                tqdm(
                    executor8.map(SSHParamiko.runsshcmd, PrivConnections.values()),
                    total=len(PrivConnections),
                    desc="Collecting Information from the switches",
                    ascii=True,
                    bar_format="{l_bar}{bar}|",
                )
            )


if __name__ == "__main__":

    start = time.time()
    resultpath = dirinit()
    config_files = InputParser()
    config_files.check_input_files()
    config_files.input_parser()
    run()
    coll = str(len("Collecting Information from the switches"))
    with tqdm(
        total=1,
        file=sys.stdout,
        desc="Parsing switches Information",
        ascii=True,
        bar_format="{desc:37}: {percentage:3.0f}%|{bar}|",
    ) as pbar:
        parser = Parser()
        data = parser.file_parse()
        pbar.update()
    with tqdm(
        total=1,
        file=sys.stdout,
        desc="Genrating report",
        ascii=True,
        bar_format="{desc:37}: {percentage:3.0f}%|{bar}|",
    ) as pbar:
        parser.reporter(data)
        pbar.update()
    dirend()
    print("Reports have been generated in the following path : %s" % resultpath)

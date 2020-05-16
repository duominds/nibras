__version__ = "1.0.0"

import os.path
import re
import sys
import json
from datetime import datetime


class Parser:
    def file_exists(self, file_path, line_number):
        if os.path.isfile(file_path):
            with open(file_path, "r") as fr:
                file_lines = fr.readlines()
                if len(file_lines) < line_number:
                    return False
                else:
                    return True
        else:
            return False

    def file_parse(self):
        self.switch_holder = dict()
        rootabspath = os.path.abspath(".")
        dataabspath = os.path.abspath(os.path.join(rootabspath, "data"))
        dt = datetime.today().strftime("%Y-%m-%d")
        today_date = os.path.abspath(os.path.join(dataabspath, dt))
        total_asset_set = set()
        local_mac_addresses = set()
        for file in os.listdir(today_date):
            if not file.startswith("."):
                switch_key = file.split("-")[0]
                with open(today_date + "/" + file) as f:
                    first_line = f.readline()
                    if ("Error 100" or "Error 200" or "Error 300") not in first_line:
                        if self.file_exists(today_date + "/" + file, 80):
                            content = open(today_date + "/" + file, "r").read()
                            mac_addresses = re.findall(
                                "address\sis\s(([0-9a-f].?){12})", content, re.M
                            )
                            for mac_elem in mac_addresses:
                                local_mac_addresses.add(mac_elem[0].rstrip())
        for file in os.listdir(today_date):
            if not file.startswith("."):
                switch_key = file.split("-")[0]
                with open(today_date + "/" + file) as f:
                    first_line = f.readline()
                    if ("Error 100" or "Error 200" or "Error 300") in first_line:
                        self.switch_holder = {
                            switch_key: {
                                "version": "N/A",
                                "Enable password": "N/A",
                                "Trunk ports": "N/A",
                                "users": "N/A",
                                "interfaces": "N/A",
                                "Switch total assets": "N/A",
                            }
                        }
                    else:
                        if self.file_exists(today_date + "/" + file, 80):
                            switch_key = file.split("-")[0]
                            with open(today_date + "/" + file, "r") as switch_file:
                                line = next(switch_file)

                                version_regex = re.compile(
                                    r"^Cisco IOS Software.*Version(.+?),"
                                )
                                enable_regex = re.compile(r"enable\ssecret")
                                user_regex = re.compile(r"username\s([^\s]+)\s")
                                mac_regex = re.compile(
                                    r"\s+\d+\s+(([0-9a-f].?){12})\s+\w+\s+([^\s]+)"
                                )
                                trunk_regex = re.compile(r"[\w\W]+\s+trunking\s+")

                                int_mac_hash = dict()
                                switch_mac_set = set()
                                enable_password = "false"
                                users = []
                                trunk_counter = 0
                                while line:
                                    if version_regex.match(line):
                                        match_pat = version_regex.match(line)
                                        version = match_pat.group(1)
                                        version = version.lstrip()
                                        ios_version = {"version": version}

                                    elif enable_regex.match(line):
                                        enable_password = "true"

                                    elif user_regex.match(line):
                                        match_pat = user_regex.match(line)
                                        users.append(match_pat.group(1))

                                    elif trunk_regex.match(line):
                                        trunk_counter += 1

                                    elif mac_regex.match(line):
                                        match_pat = mac_regex.match(line)

                                        if match_pat.group(3) not in int_mac_hash:

                                            int_mac_hash[match_pat.group(3)] = [
                                                match_pat.group(1).rstrip()
                                            ]
                                        else:

                                            int_mac_hash[match_pat.group(3)].append(
                                                match_pat.group(1).rstrip()
                                            )
                                        if (
                                            match_pat.group(1).rstrip()
                                            not in local_mac_addresses
                                        ):
                                            switch_mac_set.add(
                                                match_pat.group(1).rstrip()
                                            )
                                            total_asset_set.add(
                                                match_pat.group(1).rstrip()
                                            )

                                        # print(switch_mac_set)
                                    line = next(switch_file, None)

                        if version:
                            self.switch_holder[switch_key] = ios_version
                        self.switch_holder[switch_key].update(
                            {"Enable password": enable_password}
                        )
                        self.switch_holder[switch_key].update(
                            {"Trunk ports": trunk_counter}
                        )
                        users_data = dict()
                        users_data["users"] = users
                        self.switch_holder[switch_key].update(users_data)
                        interfaces_hash = dict()
                        interfaces_hash["interfaces"] = int_mac_hash
                        self.switch_holder[switch_key].update(interfaces_hash)
                        self.switch_holder[switch_key]["Switch total assets"] = len(
                            switch_mac_set
                        )

        assets_counter = 0

        self.switch_holder["Total assets"] = len(total_asset_set)

        return self.switch_holder

    def reporter(self, switches_data):
        assets_counter = switches_data["Total assets"]
        # Create json file for the output
        today_date = datetime.today().strftime("%Y-%m-%d")
        with open("output/{}_result.json".format(today_date), "w") as f:
            json.dump(switches_data, f)

        # Create XLS file
        switches = []
        versions = []
        enable_pass = []
        switch_total_assets = []
        trunk_ports = []
        for k in switches_data:
            if k != "Total assets":
                switches.append(k)
                if "version" in switches_data[k]:
                    versions.append(switches_data[k]["version"])
                if "Enable password" in switches_data[k]:
                    enable_pass.append(switches_data[k]["Enable password"])
                if "Switch total assets" in switches_data[k]:
                    switch_total_assets.append(switches_data[k]["Switch total assets"])
                if "Trunk ports" in switches_data[k]:
                    trunk_ports.append(switches_data[k]["Trunk ports"])

        switches.insert(0, "Switch")  # A
        versions.insert(0, "IOS version")  # B
        enable_pass.insert(0, "Enable password")  # C
        trunk_ports.insert(0, "Total trunk port(s)")  # E
        switch_total_assets.insert(0, "Switch total assets")  # F

        import xlsxwriter

        workbook = xlsxwriter.Workbook("output/{}_result.xlsx".format(today_date))
        worksheet = workbook.add_worksheet()

        assets = workbook.add_format(
            {"bold": True, "align": "center", "font_size": 20, "font_color": "green"}
        )
        header = workbook.add_format({"bold": True, "align": "center", "font_size": 14})

        worksheet.set_column("A:A", 20, header)
        worksheet.set_column("B:B", 20, header)
        worksheet.set_column("C:C", 20, header)
        worksheet.set_column("D:D", 25, header)
        worksheet.set_column("E:E", 25, header)
        worksheet.set_column("F:F", 20, header)

        for i, elem in enumerate(switches, 1):
            worksheet.write("A{}".format(i), elem)
        for i, elem in enumerate(versions, 1):
            worksheet.write("B{}".format(i), elem)
        for i, elem in enumerate(enable_pass, 1):
            worksheet.write("C{}".format(i), elem)
        for i, elem in enumerate(switch_total_assets, 1):
            worksheet.write("D{}".format(i), elem)
        for i, elem in enumerate(trunk_ports, 1):
            worksheet.write("E{}".format(i), elem)
        worksheet.write("F1", "Total assets")
        worksheet.write("F2", assets_counter, assets)

        workbook.close()

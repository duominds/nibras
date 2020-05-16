__version__ = "1.0.0"

import xlrd
import os
import sys
import csv
import yaml


class InputParser:
    def __init__(self):
        self.input_files = os.listdir("input")

    def check_input_files(self):
        self.input_files = [
            elem for elem in self.input_files if not elem.startswith(".")
        ]

        if len(self.input_files) == 0:
            print("No input file was provided exiting")
            sys.exit()
        if len(self.input_files) > 1:
            print("Multiple files were provided.. Exiting")
            sys.exit()

    def input_parser(self):
        if "csv" in self.input_files[0]:
            if os.path.exists("input/input.csv"):
                self.switchs_ips = []
                self.usernames = []
                self.passwords = []
                self.secret = []
                self.port = []

                with open("input/input.csv", "rt") as f:
                    data = csv.reader(f)
                    ncol = len(next(data))
                    if ncol < 5:
                        print(
                            "Please make sure you filled the CSV file correctly, for instructions please check README file"
                        )
                        sys.exit()
                    f.seek(0)
                    for row in data:
                        self.switchs_ips.append(row[0])
                        self.usernames.append(row[1])
                        self.passwords.append(row[2])
                        self.secret.append(row[3])
                        self.port.append(row[4])

                if "" in set(self.switchs_ips):
                    print(
                        "An empty IP was provided please check the input file and execute the script again"
                    )
                    sys.exit()
                if "" in set(self.usernames):
                    print(
                        "An empty username was provided please check the input file and execute the script again"
                    )
                    sys.exit()
                if "" in set(self.passwords):
                    print(
                        "An empty password was provided please check the input file and execute the script again"
                    )
                    sys.exit()
                if "" in set(self.secret):
                    print(
                        "An empty enable password was provided please check the input file and execute the script again"
                    )
                    sys.exit()
                if "" in set(self.port):
                    print(
                        "An empty port was provided please check the input file and execute the script again"
                    )
                    sys.exit()
                self.main_dict = {
                    elem: {
                        "user": None,
                        "password": None,
                        "secret": None,
                        "port": None,
                    }
                    for elem in self.switchs_ips
                }

                for i, elem in enumerate(self.switchs_ips):
                    self.main_dict[elem]["user"] = self.usernames[i]
                    self.main_dict[elem]["password"] = self.passwords[i]
                    self.main_dict[elem]["secret"] = self.secret[i]
                    self.main_dict[elem]["port"] = int(self.port[i])

                with open(r"config/results.yaml", "w") as file:
                    documents = yaml.dump(self.main_dict, file)

                return True
            else:
                print("No input.csv file was found in input folder ... Exiting")
                sys.exit()

        elif "xlsx" in self.input_files[0]:
            if os.path.exists("input/input.xlsx"):
                xls_file = "input/input.xlsx"
                wb = xlrd.open_workbook(xls_file)
                sheet = wb.sheet_by_index(0)
                sheet.cell_value(0, 0)
                self.switchs_ips = []
                self.usernames = []
                self.passwords = []
                self.secret = []
                self.port = []

                if sheet.ncols < 5:
                    print(
                        "Please make sure you filled the XLS file correctly, for instructions please check README file"
                    )
                    sys.exit()
                for i in range(sheet.nrows):
                    self.switchs_ips.append(sheet.cell_value(i, 0))
                    self.usernames.append(sheet.cell_value(i, 1))
                    self.passwords.append(sheet.cell_value(i, 2))
                    self.secret.append(sheet.cell_value(i, 3))
                    self.port.append(int(sheet.cell_value(i, 4)))

                if "" in set(self.switchs_ips):
                    print(
                        "An empty IP was provided please check the input file and execute the script again"
                    )
                    sys.exit()
                if "" in set(self.usernames):
                    print(
                        "An empty username was provided please check the input file and execute the script again"
                    )
                    sys.exit()
                if "" in set(self.passwords):
                    print(
                        "An empty password was provided please check the input file and execute the script again"
                    )
                    sys.exit()
                if "" in set(self.secret):
                    print(
                        "An empty enable password was provided please check the input file and execute the script again"
                    )
                    sys.exit()
                if "" in set(self.port):
                    print(
                        "An empty port was provided please check the input file and execute the script again"
                    )
                    sys.exit()
                self.main_dict = {
                    elem: {
                        "user": None,
                        "password": None,
                        "secret": None,
                        "port": None,
                    }
                    for elem in self.switchs_ips
                }

                for i, elem in enumerate(self.switchs_ips):
                    self.main_dict[elem]["user"] = self.usernames[i]
                    self.main_dict[elem]["password"] = self.passwords[i]
                    self.main_dict[elem]["secret"] = self.secret[i]
                    self.main_dict[elem]["port"] = int(self.port[i])

                with open(r"config/results.yaml", "w") as file:
                    documents = yaml.dump(self.main_dict, file)

                return True
            else:
                print("No input.xlsx file was found in input folder ... Exiting")
                sys.exit()
        else:
            print(
                "No input files were found, please make sure you have input.xlsx or input.csv inside input folder before running the tool"
            )
            sys.exit()

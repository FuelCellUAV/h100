#! /usr/bin/python3

"""Check for input every 0.1 seconds. Treat available input
immediately, but do something else if idle."""

import sys
import select
import time


class UserInterface(object):
    def __init__(self):
        # files monitored for input
        self.__read_list = [sys.stdin]
        self.__repeat_command_list = []
        self.__one_off_command_list = []

    # These commands will be run on each iteration loop
    @property
    def repeat_command_list(self):
        return self.__repeat_command_list

    @repeat_command_list.setter
    def repeat_command_list(self, new_fun):
        self.__repeat_command_list.append(new_fun)

    # These commands will be run on each iteration loop
    @property
    def one_off_command_list(self):
        return self.__one_off_command_list

    @repeat_command_list.setter
    def one_off_command_list(self, new_fun):
        self.__one_off_command_list.append(new_fun)

    # MAIN
    def run(self):
        for fun in self.command_list:
            fun()
        for fun in self.one_off_command_list:
            fun()
        self.__one_off_command_list = []




    # Read user input
    @staticmethod
    def _getline(read_list):
        ready = select.select(read_list, [], [], 0.001)[0]
        if not ready:
            return ''
        else:
            for file in ready:
                line = file.readline()
                if not line:  # EOF, remove file from input list
                    pass
                elif line.rstrip():  # optional: skipping empty lines
                    return line.lower()
        return ''


global ui
ui = UserInterface()

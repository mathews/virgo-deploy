## -*- coding: utf-8 -*-
"""
Created on Sat Feb 20 00:32:38 2016

@author: mathews
"""

from bladerunner.base import Bladerunner
from bladerunner.formatting import csv_results, pretty_results, stacked_results

def bladerunner_test():
    """A simple test of bladerunner's execution and output formats."""

    # pass in lists of strings, commands and hosts will be executed in order
    servers = ["localhost"]
    commands = ["ls"]

    # this is the full options dictionary
    options = {
        "debug": False,
        "delay": None,
        "cmd_timeout": 20,
        "csv_char": ",",
        #"output_file": "/home/mathews/Documents/output.txt",
        "passwd_prompts": [],  # usually best to let Bladerunner decide
        "password": "springsource",
        "password_safety": True,
        "port": 2403,
        "progressbar": True,
        "second_password": "super-sekrets",
        "shell_prompts": [],  # this list is typically auto-generated
        "ssh": "ssh",
        "ssh_key": None,
        "stacked": False,  # preference flag for stacked results
        "style": 0,
        "threads": 100,
        "timeout": 20,
        "unix_line_endings": False,
        "username": "admin",
        "width": 80,  # used in displaying results
        "windows_line_endings": False,  # force the use of \r\n
    }

    # initialize Bladerunner with the options provided
    runner = Bladerunner(options)

    # execution of commands on hosts, may take a while to return
    results = runner.run(commands, servers)

    # Prints CSV results
    csv_results(results)

    # Prints pretty_results using the available styles
    for i in range(4):
        options["style"] = i
        pretty_results(results, options)

    # Prints the results in a flat, vertically stacked way
    stacked_results(results)


bladerunner_test()
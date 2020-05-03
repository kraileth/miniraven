#############
 # Imports #
#############

import modules.globalvars as globalvars
import modules.helpers as helpers
import os

###############
 # Functions #
###############

def assert_conf_file_present():
    ("Config: Checking if config file exists... ")
    if not os.path.isfile(globalvars.CONFNAME):
        helpers.die("\nError: Could not read configuration file \"" + globalvars.CONFNAME + "\"! Exiting.")
    helpers.verbose_output("ok\n")

def assert_conf_section_present(section):
    helpers.verbose_output("Config: Checking for section \"" + section + "\"... ")
    if section not in config.sections():
        helpers.die("\nError: Cannot find section \"" + section + "\" in configuration file \"" + CONFNAME + "\"! Exiting.")
    helpers.verbose_output("ok\n")

def main():
    print("This module is meant to be used with MiniRaven and not really useful on it's own.")
    exit(0)

if __name__ == "__main__":
    main()

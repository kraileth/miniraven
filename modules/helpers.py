#############
 # Imports #
#############

import globalvars
import modules.conf as conf
import os
import subprocess

###############
 # Functions #
###############

def die(msg):
    print(msg)
    exit(1)

def verbose_output(string):
    if globalvars.VERBOSE:
        print(string, end="", flush=True)

def get_cmd_output(cmd, params):
    p = subprocess.Popen(cmd + " " + params, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.readlines()[0].strip().decode()

def assert_external_binaries_available():
    for b in conf.get_config_value('main', 'external_binaries').split(', '):
        verbose_output("Programs: Checking if \"" + b + "\" is available... ")
        p = subprocess.Popen('command -v ' + b, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if p.stdout.readlines() == []:
            die("\nError: \"" + b + "\" is not available on this system (or not in PATH)! Exiting.")
        verbose_output("ok\n")
    print("Programs: All required external programs are available.")

def ensure_fs_hierarchy(hier):
    for d in conf.get_config_value('fs', hier + '_hier').split(', '):
        directory = conf.get_config_value('fs', hier + '_' + d)
        verbose_output("Filesystem: Ensuring directory \"" + directory + "\" exists... ")
        if not os.path.isdir(directory):
            try:
                os.makedirs(directory)
            except OSError as e:
                die("\nFilesystem error: Could not create directory \"" + directory + "\"! Exiting.")
        verbose_output("ok\n")

def ensure_fs():
    ensure_fs_hierarchy('rjail')
    ensure_fs_hierarchy('rbuild')
    print("Filesystem: Hierarchy is in place.")

def main():
    print("This module is meant to be used with MiniRaven and not really useful on it's own.")
    exit(0)

##########
 # Main #
##########

if __name__ == "__main__":
    main()

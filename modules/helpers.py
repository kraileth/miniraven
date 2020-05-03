#############
 # Imports #
#############

import globalvars

###############
 # Functions #
###############

def die(msg):
    print(msg)
    exit(1)

def verbose_output(string):
    if globalvars.VERBOSE:
        print(string, end="", flush=True)

def main():
    print("This module is meant to be used with MiniRaven and not really useful on it's own.")
    exit(0)

##########
 # Main #
##########

if __name__ == "__main__":
    main()

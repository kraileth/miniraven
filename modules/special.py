#############
 # Imports #
#############

import globalvars
import modules.misc as misc
import re
import socket
import time

###############
 # Functions #
###############

def prepare_bmake_patch():
    misc.verbose_output("Adapting bmake patch to target system... ")
    for s in ["OSNAME", "OSVERSION", "OSRELEASE", "OSMAJOR", "OSARCH", "STDARCH"]:
        misc.reinplace(globalvars.SUBSTITUTION_MAP['rbuild_patches_dir'] + "/bmake/patch-main.c", s, eval("globalvars." + s))
    misc.verbose_output("ok\n")

def prepare_uname_source():
    wrkdir = misc.get_wrkdir("uname")
    misc.verbose_output("Applying plattform info to fake uname... ")
    misc.reinplace(wrkdir + "/uname.c.in", "\"@OPSYS@\"", globalvars.OSNAME)
    misc.reinplace(wrkdir + "/uname.c.in", "\"@ARCH@\"", globalvars.OSARCH)
    misc.reinplace(wrkdir + "/uname.c.in", "\"@PLATFORM@\"", globalvars.STDARCH)
    misc.reinplace(wrkdir + "/uname.c.in", "\"@RELEASE@\"", globalvars.OSRELEASE + "-RAVEN")
    misc.reinplace(wrkdir + "/uname.c.in", "\"@USERVER@\"", globalvars.OSVERSION)
    misc.reinplace(wrkdir + "/uname.c.in", "\"@OPSYS@ @RELEASE@ #0 Sat Jul 29 09:00:00 CDT 2017 root@octavia.unreal.systems:/usr/obj/usr/src/sys/GENERIC\"", globalvars.OSNAME + " " + globalvars.OSRELEASE + " #0 " + time.ctime() + " root@" + socket.getfqdn() + ":/usr/obj/usr/src/sys/GENERIC")
    misc.reinplace(wrkdir + "/uname.c.in", "\"octavia.unreal.systems\"", socket.getfqdn())
    misc.verbose_output("ok\n")

def main():
    print("This module is meant to be used with MiniRaven and not really useful on it's own.")
    exit(0)

if __name__ == "__main__":
    main()

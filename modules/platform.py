#############
 # Imports #
#############

import globalvars
import modules.misc as misc
import modules.conf as conf

###############
 # Functions #
###############

def get_osname():
    if conf.get_config_value('platform', 'osname') == '' or conf.get_config_value('platform', 'osname') == 'auto':
        osname = misc.get_cmd_output("uname", "-s")
        misc.verbose_output("System: Autodetecting OS... " + osname + "\n")
        return osname
    else:
        osname = conf.get_config_value('platform', 'osname')
        misc.verbose_output("System: OS is \"" + osname + "\" (override via config file)\n")
        return osname

def get_os_release():
    if conf.get_config_value('platform', 'osrelease') == '' or conf.get_config_value('platform', 'osrelease') == 'auto':
        if globalvars.OSNAME in ['DragonFly', 'FreeBSD']:
            temp = misc.get_cmd_output("uname", "-r")
            osrelease = temp[:temp.find("-")]
        elif globalvars.OSNAME == 'NetBSD':
            osrelease = misc.get_cmd_output("uname", "-r")
        else:
            misc.die("FATAL: INCOMPLETELY SUPPORTED OS! THIS IS A BUG.")
        misc.verbose_output("System: Autodetecting OS release... " + osrelease + "\n")
        return osrelease
    else:
        osrelease = conf.get_config_value('platform', 'osrelease')
        misc.verbose_output("System: OS release is \"" + osrelease + "\" (override via config file)\n")
        return osrelease

def get_os_version():
    if conf.get_config_value('platform', 'osversion') == '' or conf.get_config_value('platform', 'osversion') == 'auto':
        if globalvars.OSNAME in ['DragonFly', 'NetBSD']:
            major = globalvars.OSRELEASE[:globalvars.OSRELEASE.find(".")]
            minor = globalvars.OSRELEASE[globalvars.OSRELEASE.find(".") + 1:]
            if len(major) == 1:
                maj = major + "00"
            elif len(major) == 2:
                maj = major + "0"
            else:
                maj = major
            if len(minor) == 1:
                mnr = minor + "00"
            elif len(minor) == 2:
                mnr = minor + "0"
            else:
                mnr = minor
            osversion = maj + mnr
        elif globalvars.OSNAME == 'FreeBSD':
            osversion = misc.get_cmd_output("uname", "-K")
        else:
            misc.die("FATAL: INCOMPLETELY SUPPORTED OS! THIS IS A BUG.")
        misc.verbose_output("System: Autodetecting OS version... " + osversion + "\n")
        return osversion
    else:
        osversion = conf.get_config_value('platform', 'osversion')
        misc.verbose_output("System: OS version is \"" + osversion + "\" (override via config file)\n")
        return osversion

def get_os_major():
    if conf.get_config_value('platform', 'osmajor') == '' or conf.get_config_value('platform', 'osmajor') == 'auto':
        if globalvars.OSNAME in ['DragonFly', 'FreeBSD', 'NetBSD']:
            osmajor = globalvars.OSRELEASE[:globalvars.OSRELEASE.find(".")]
        else:
            misc.die("FATAL: INCOMPLETELY SUPPORTED OS! THIS IS A BUG.")
        misc.verbose_output("System: Autodetecting OS major version... " + osmajor + "\n")
        return osmajor
    else:
        osmajor = conf.get_config_value('platform', 'osmajor')
        misc.verbose_output("System: OS major version is \"" + osmajor + "\" (override via config file)\n")
        return osmajor

def get_os_arch():
    if conf.get_config_value('platform', 'osarch') == '' or conf.get_config_value('platform', 'osarch') == 'auto':
        if globalvars.OSNAME in ['DragonFly', 'FreeBSD', 'NetBSD']:
            osarch = misc.get_cmd_output("uname", "-p")
        else:
            misc.die("FATAL: INCOMPLETELY SUPPORTED OS! THIS IS A BUG.")
        misc.verbose_output("System: Autodetecting host architecture... " + osarch + "\n")
        return osarch
    else:
        osarch = conf.get_config_value('platform', 'osarch')
        misc.verbose_output("System: Host architecture is \"" + osarch + "\" (override via config file)\n")
        return osarch

def get_stdarch():
    if conf.get_config_value('platform', 'stdarch') == '' or conf.get_config_value('platform', 'stdarch') == 'auto':
        if globalvars.OSARCH == "amd64" or globalvars.OSARCH == "x86_64":
            stdarch = "x86_64"
        elif globalvars.OSARCH == "i386":
            stdarch = "x86"
        elif globalvars.OSARCH == "aarch64" or OSARCH == "arm64":
            stdarch = "aarch64"
        else:
            misc.die("System: Error, unsupported architecture \"" + OSARCH + "\"!")
        misc.verbose_output("System: Autodetecting host standard architecture... " + stdarch + "\n")
        return stdarch
    else:
        stdarch = conf.get_config_value('platform', 'stdarch')
        misc.verbose_output("System: Host standard architecture is \"" + stdarch + "\" (override via config file)\n")
        return stdarch

def assemble_triple():
    if conf.get_config_value('platform', 'tgt_triple') == '' or conf.get_config_value('platform', 'tgt_triple') == 'auto':
        if globalvars.OSNAME == 'DragonFly':
            tgt_triple = globalvars.STDARCH + "-raven-" + globalvars.OSNAME.lower() + globalvars.OSRELEASE
        elif globalvars.OSNAME == 'FreeBSD' or globalvars.OSNAME == 'NetBSD':
            tgt_triple = globalvars.STDARCH + "-raven-" + globalvars.OSNAME.lower() + globalvars.OSMAJOR
        else:
            misc.die("FATAL: INCOMPLETELY SUPPORTED OS! THIS IS A BUG.")
        misc.verbose_output("System: Assembling target triple... " + tgt_triple + "\n")
        return tgt_triple
    else:
        tgt_triple = conf.get_config_value('platform', 'tgt_triple')
        misc.verbose_output("System: Target triple is \"" + tgt_triple + "\" (override via config file)\n")
        return tgt_triple

def main():
    print("This module is meant to be used with MiniRaven and not really useful on it's own.")
    exit(0)

if __name__ == "__main__":
    main()

#############
 # Imports #
#############

import globalvars
import modules.helpers as helpers
import modules.conf as conf

###############
 # Functions #
###############

def get_osname():
    if conf.get_config_value('version', 'osname') == '' or conf.get_config_value('version', 'osname') == 'auto':
        osname = helpers.get_cmd_output("uname", "-s")
        helpers.verbose_output("System: Autodetecting OS... " + osname + "\n")
        return osname
    else:
        osname = conf.get_config_value('version', 'osname')
        helpers.verbose_output("System: OS is \"" + osname + "\" (override via config file)\n")
        return osname

def get_os_version():
    if conf.get_config_value('version', 'osversion') == '' or conf.get_config_value('version', 'osversion') == 'auto':
        if globalvars.OSNAME == 'FreeBSD':
            osversion = helpers.get_cmd_output("uname", "-K")
            helpers.verbose_output("System: Autodetecting OS version... " + osversion + "\n")
            return osversion
        else:
            helpers.die("FATAL: INCOMPLETELY SUPPORTED OS! THIS IS A BUG.")
    else:
        osversion = conf.get_config_value('version', 'osversion')
        helpers.verbose_output("System: OS version is \"" + osversion + "\" (override via config file)\n")
        return osversion

def get_os_release():
    if conf.get_config_value('version', 'osrelease') == '' or conf.get_config_value('version', 'osrelease') == 'auto':
        if globalvars.OSNAME == 'FreeBSD':
            temp = helpers.get_cmd_output("uname", "-v")
            osrelease = temp[temp.find(" ") + 1 : temp.find("-")]
            helpers.verbose_output("System: Autodetecting OS release... " + osrelease + "\n")
            return osrelease
        else:
            helpers.die("FATAL: INCOMPLETELY SUPPORTED OS! THIS IS A BUG.")
    else:
        osrelease = conf.get_config_value('version', 'osrelease')
        helpers.verbose_output("System: OS release is \"" + osrelease + "\" (override via config file)\n")
        return osrelease

def get_os_major():
    if conf.get_config_value('version', 'osmajor') == '' or conf.get_config_value('version', 'osmajor') == 'auto':
        if globalvars.OSNAME == 'FreeBSD':
            osmajor = globalvars.OSRELEASE[:globalvars.OSRELEASE.find(".")]
            helpers.verbose_output("System: Autodetecting OS major version... " + osmajor + "\n")
            return osmajor
        else:
            helpers.die("FATAL: INCOMPLETELY SUPPORTED OS! THIS IS A BUG.")
    else:
        osmajor = conf.get_config_value('version', 'osmajor')
        helpers.verbose_output("System: OS major version is \"" + osmajor + "\" (override via config file)\n")
        return osmajor

def get_os_arch():
    if conf.get_config_value('version', 'osarch') == '' or conf.get_config_value('version', 'osarch') == 'auto':
        if globalvars.OSNAME == 'FreeBSD':
            osarch = helpers.get_cmd_output("uname", "-p")
            helpers.verbose_output("System: Autodetecting host architecture... " + osarch + "\n")
            return osarch
        else:
            helpers.die("FATAL: INCOMPLETELY SUPPORTED OS! THIS IS A BUG.")
    else:
        osarch = conf.get_config_value('version', 'osarch')
        helpers.verbose_output("System: Host architecture is \"" + osarch + "\" (override via config file)\n")
        return osarch

def get_stdarch():
    if conf.get_config_value('version', 'stdarch') == '' or conf.get_config_value('version', 'stdarch') == 'auto':
        if globalvars.OSARCH == "amd64" or globalvars.OSARCH == "x86_64":
            stdarch = "x86_64"
        elif globalvars.OSARCH == "i386":
            stdarch = "x86"
        elif globalvars.OSARCH == "aarch64" or OSARCH == "arm64":
            stdarch = "aarch64"
        else:
            helpers.die("System: Error, unsupported architecture \"" + OSARCH + "\"!")
        helpers.verbose_output("System: Autodetecting host standard architecture... " + stdarch + "\n")
        return stdarch
    else:
        stdarch = conf.get_config_value('version', 'stdarch')
        helpers.verbose_output("System: Host standard architecture is \"" + stdarch + "\" (override via config file)\n")
        return stdarch

def assemble_triple():
    if conf.get_config_value('version', 'tgt_triple') == '' or conf.get_config_value('version', 'tgt_triple') == 'auto':
        if globalvars.OSNAME == 'FreeBSD':
            tgt_triple = globalvars.STDARCH + "-raven-" + globalvars.OSNAME.lower() + globalvars.OSMAJOR
            helpers.verbose_output("System: Assembling target triple... " + tgt_triple + "\n")
            return tgt_triple
        else:
            helpers.die("FATAL: INCOMPLETELY SUPPORTED OS! THIS IS A BUG.")
    else:
        tgt_triple = conf.get_config_value('version', 'tgt_triple')
        helpers.verbose_output("System: Target triple is \"" + tgt_triple + "\" (override via config file)\n")
        return tgt_triple

def main():
    print("This module is meant to be used with MiniRaven and not really useful on it's own.")
    exit(0)

if __name__ == "__main__":
    main()

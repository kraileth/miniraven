#############
 # Imports #
#############

import globalvars
import modules.misc as misc
import modules.subst as subst
import os

###############
 # Functions #
###############

def assert_conf_file_present():
    ("Config: Checking if config file exists... ")
    if not os.path.isfile(globalvars.CONFNAME):
        misc.die("\nError: Could not read configuration file \"" + globalvars.CONFNAME + "\"! Exiting.")
    misc.verbose_output("ok\n")

def assert_conf_section_present(section):
    misc.verbose_output("Config: Checking for section \"" + section + "\"... ")
    if section not in config.sections():
        misc.die("\nError: Cannot find section \"" + section + "\" in configuration file \"" + CONFNAME + "\"! Exiting.")
    misc.verbose_output("ok\n")

def assert_key_in_conf_section(section, key, not_empty):
    misc.verbose_output("Config: Checking for key \"" + key + "\" in " + section + "... ")
    if not key in config[section]:
        misc.die("\nConfiguration error: Key \"" + key + "\" missing in section \"" + section + "\"! Exiting.")
    if not_empty and config[section][key] == '':
        misc.die("\nConfiguration error: Key \"" + key + "\" exists in section \"" + section + "\" but is not allowed to be empty! Exiting.")
    misc.verbose_output("ok\n")

def assert_config_keys(section, data):
    assert_conf_section_present(section)
    for key in data:
        assert_key_in_conf_section(section, key, data[key])

def get_config_value(section, key):
    if not section in config.sections():
        misc.die("Error: Cannot get config values, section \"" + section + "\" does not exist! Exiting.")
    if not key in config[section]:
        misc.die("Error: Cannot get config values, no key \"" + key + "\" in section \"" + section + "\"! Exiting.")
    value = config[section][key]
    if len(subst.get_substitution_variables(value)) > 0:
        return(subst.substitute_variables(value))
    else:
        return(value)

def assert_package_keys_in_section(section):
    for p in get_config_value('main', 'packages').split(', '):
        assert_key_in_conf_section(section, p, True)

def assert_config_valid():
    assert_config_keys('main', globalvars.MAIN_KEYS)
    assert_config_keys('fs', globalvars.FS_KEYS)
    assert_config_keys('version', globalvars.VERSION_KEYS)
    assert_config_keys('decompress', {'file_types' : False})
    for s in get_config_value('main', 'package_sections').split(', '):
        assert_conf_section_present(s)
    assert_package_keys_in_section('mini_manifest')
    assert_package_keys_in_section('install_cmds')
    print("Config: Configuration is valid.")

def main():
    print("This module is meant to be used with MiniRaven and not really useful on it's own.")
    exit(0)

if __name__ == "__main__":
    main()

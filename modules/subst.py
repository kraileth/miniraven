#############
 # Imports #
#############

import globalvars
import modules.conf as conf
import modules.misc as misc

###############
 # Functions #
###############

def get_substitution_variables(string):
    variables = []
    if "$$" in string:
        var_pos = [pos for pos in range(len(string)) if string.find("$$", pos) == pos]
        if string.find("$$$") != -1:                                    # Avoid second $$ position if another variable begins right after one ends
            var_pos.remove(string.find("$$$") + 1)
        if len(var_pos) % 2 != 0:                                       # Invalid use of $$!
            misc.die("Error: Invalid variable substitution in string \"" + string + "\"!")
        if len(var_pos) > 0:
            for v in range(0, int(len(var_pos))):
                if v % 2 != 0:
                    variables.append(string[var_pos[v - 1]:var_pos[v] + 2].replace('$$', ''))
    return(variables)

def get_substitution_variable_value(var):
    v = var.lower()
    if not v in globalvars.SUBSTITUTION_MAP:
        misc.die("Error: Variable \"$$" + var + "$$\" not found in substitution map! Exiting.")
    return(globalvars.SUBSTITUTION_MAP[v])

def substitute_variables(string):
    for var in get_substitution_variables(string):
        string = string.replace("$$" + var + "$$", get_substitution_variable_value(var), 1)
    return(string)

def populate_substitution_map():
    misc.verbose_output("Internal: Populating substitution map... ")
    for v in conf.get_config_value('main', 'substitution_vars').split(', '):
        globalvars.SUBSTITUTION_MAP[v] = conf.get_config_value('fs', v)
    for l in conf.get_config_value('main', 'substitution_lists').split(', '):
        for v in conf.get_config_value('fs', l).split(', '):
            varname = l.replace('_hier', '') + '_' + v
            globalvars.SUBSTITUTION_MAP[varname] = conf.get_config_value('fs', varname)
    misc.verbose_output("ok\n")

def main():
    print("This module is meant to be used with MiniRaven and not really useful on it's own.")
    exit(0)

if __name__ == "__main__":
    main()

#############
 # Imports #
#############

import globalvars
import modules.helpers as helpers

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
            helpers.die("Error: Invalid variable substitution in string \"" + string + "\"!")
        if len(var_pos) > 0:
            for v in range(0, int(len(var_pos))):
                if v % 2 != 0:
                    variables.append(string[var_pos[v - 1]:var_pos[v] + 2].replace('$$', ''))
    return(variables)

def get_substitution_variable_value(var):
    v = var.lower()
    if not v in globalvars.SUBSTITUTION_MAP:
        helpers.die("Error: Variable \"$$" + var + "$$\" not found in substitution map! Exiting.")
    return(globalvars.SUBSTITUTION_MAP[v])

def substitute_variables(string):
    for var in get_substitution_variables(string):
        string = string.replace("$$" + var + "$$", get_substitution_variable_value(var), 1)
    return(string)

def main():
    print("This module is meant to be used with MiniRaven and not really useful on it's own.")
    exit(0)

if __name__ == "__main__":
    main()

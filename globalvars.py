#############
 # Globals #
#############

VERBOSE                     = True
CONFNAME                    = 'nest.conf'
MAIN_KEYS                   = {'external_binaries'  : False,
                               'substitution_vars'  : False,
                               'substitution_lists' : False,
                               'package_sections'   : True,
                               'packages'           : True}
FS_KEYS                     = {'tgt_prefix'         : True,
                               'rjail_root'         : True,
                               'rjail_hier'         : True,
                               'rbuild_root'        : True,
                               'rbuild_hier'        : True}
VERSION_KEYS                = {'osname'             : False,
                               'osversion'          : False,
                               'osrelease'          : False,
                               'osmajor'            : False,
                               'osarch'             : False,
                               'stdarch'            : False,
                               'tgt_triple'         : False}
OPERATING_SYSTEMS_SUPPORTED = ['FreeBSD']
SUBSTITUTION_MAP            = {}

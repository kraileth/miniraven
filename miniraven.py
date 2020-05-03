#!/usr/local/bin/python3.7

#############
 # Imports #
#############

import modules.globalvars as globalvars
import modules.helpers as helpers
import configparser
import hashlib
import os
import re
import shutil
import socket
import subprocess
import time
from urllib.request import urlretrieve

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

def assert_key_in_conf_section(section, key, not_empty):
    helpers.verbose_output("Config: Checking for key \"" + key + "\" in " + section + "... ")
    if not key in config[section]:
        helpers.die("\nConfiguration error: Key \"" + key + "\" missing in section \"" + section + "\"! Exiting.")
    if not_empty and config[section][key] == '':
        helpers.die("\nConfiguration error: Key \"" + key + "\" exists in section \"" + section + "\" but is not allowed to be empty! Exiting.")
    helpers.verbose_output("ok\n")

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

def get_config_value(section, key):
    if not section in config.sections():
        helpers.die("Error: Cannot get config values, section \"" + section + "\" does not exist! Exiting.")
    if not key in config[section]:
        helpers.die("Error: Cannot get config values, no key \"" + key + "\" in section \"" + section + "\"! Exiting.")
    value = config[section][key]
    if len(get_substitution_variables(value)) > 0:
        return(substitute_variables(value))
    else:
        return(value)

def assert_config_keys(section, data):
    assert_conf_section_present(section)
    for key in data:
        assert_key_in_conf_section(section, key, data[key])

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

def get_cmd_output(cmd, params):
    p = subprocess.Popen(cmd + " " + params, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.readlines()[0].strip().decode()

def get_osname():
    if get_config_value('version', 'osname') == '' or get_config_value('version', 'osname') == 'auto':
        osname = get_cmd_output("uname", "-s")
        helpers.verbose_output("System: Autodetecting OS... " + osname + "\n")
        return osname
    else:
        osname = get_config_value('version', 'osname')
        helpers.verbose_output("System: OS is \"" + osname + "\" (override via config file)\n")
        return osname

def get_os_version():
    if get_config_value('version', 'osversion') == '' or get_config_value('version', 'osversion') == 'auto':
        if OSNAME == 'FreeBSD':
            osversion = get_cmd_output("uname", "-K")
            helpers.verbose_output("System: Autodetecting OS version... " + osversion + "\n")
            return osversion
        else:
            helpers.die("FATAL: INCOMPLETELY SUPPORTED OS! THIS IS A BUG.")
    else:
        osversion = get_config_value('version', 'osversion')
        helpers.verbose_output("System: OS version is \"" + osversion + "\" (override via config file)\n")
        return osversion

def get_os_release():
    if get_config_value('version', 'osrelease') == '' or get_config_value('version', 'osrelease') == 'auto':
        if OSNAME == 'FreeBSD':
            temp = get_cmd_output("uname", "-v")
            osrelease = temp[temp.find(" ") + 1 : temp.find("-")]
            helpers.verbose_output("System: Autodetecting OS release... " + osrelease + "\n")
            return osrelease
        else:
            helpers.die("FATAL: INCOMPLETELY SUPPORTED OS! THIS IS A BUG.")
    else:
        osrelease = get_config_value('version', 'osrelease')
        helpers.verbose_output("System: OS release is \"" + osrelease + "\" (override via config file)\n")
        return osrelease

def get_os_major():
    if get_config_value('version', 'osmajor') == '' or get_config_value('version', 'osmajor') == 'auto':
        if OSNAME == 'FreeBSD':
            osmajor = OSRELEASE[:OSRELEASE.find(".")]
            helpers.verbose_output("System: Autodetecting OS major version... " + osmajor + "\n")
            return osmajor
        else:
            helpers.die("FATAL: INCOMPLETELY SUPPORTED OS! THIS IS A BUG.")
    else:
        osmajor = get_config_value('version', 'osmajor')
        helpers.verbose_output("System: OS major version is \"" + osmajor + "\" (override via config file)\n")
        return osmajor

def get_os_arch():
    if get_config_value('version', 'osarch') == '' or get_config_value('version', 'osarch') == 'auto':
        if OSNAME == 'FreeBSD':
            osarch = get_cmd_output("uname", "-p")
            helpers.verbose_output("System: Autodetecting host architecture... " + osarch + "\n")
            return osarch
        else:
            helpers.die("FATAL: INCOMPLETELY SUPPORTED OS! THIS IS A BUG.")
    else:
        osarch = get_config_value('version', 'osarch')
        helpers.verbose_output("System: Host architecture is \"" + osarch + "\" (override via config file)\n")
        return osarch

def get_stdarch():
    if get_config_value('version', 'stdarch') == '' or get_config_value('version', 'stdarch') == 'auto':
        if OSARCH == "amd64" or OSARCH == "x86_64":
            stdarch = "x86_64"
        elif OSARCH == "i386":
            stdarch = "x86"
        elif OSARCH == "aarch64" or OSARCH == "arm64":
            stdarch = "aarch64"
        else:
            helpers.die("System: Error, unsupported architecture \"" + OSARCH + "\"!")
        helpers.verbose_output("System: Autodetecting host standard architecture... " + stdarch + "\n")
        return stdarch
    else:
        stdarch = get_config_value('version', 'stdarch')
        helpers.verbose_output("System: Host standard architecture is \"" + stdarch + "\" (override via config file)\n")
        return stdarch

def assemble_triple():
    if get_config_value('version', 'tgt_triple') == '' or get_config_value('version', 'tgt_triple') == 'auto':
        if OSNAME == 'FreeBSD':
            tgt_triple = STDARCH + "-raven-" + OSNAME.lower() + OSMAJOR
            helpers.verbose_output("System: Assembling target triple... " + tgt_triple + "\n")
            return tgt_triple
        else:
            helpers.die("FATAL: INCOMPLETELY SUPPORTED OS! THIS IS A BUG.")
    else:
        tgt_triple = get_config_value('version', 'tgt_triple')
        helpers.verbose_output("System: Target triple is \"" + tgt_triple + "\" (override via config file)\n")
        return tgt_triple

def assert_external_binaries_available():
    for b in get_config_value('main', 'external_binaries').split(', '):
        helpers.verbose_output("Programs: Checking if \"" + b + "\" is available... ")
        p = subprocess.Popen('command -v ' + b, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if p.stdout.readlines() == []:
            helpers.die("\nError: \"" + b + "\" is not available on this system (or not in PATH)! Exiting.")
        helpers.verbose_output("ok\n")
    print("Programs: All required external programs are available.")

def populate_substitution_map():
    globalvars.SUBSTITUTION_MAP
    helpers.verbose_output("Internal: Populating substitution map... ")
    for v in get_config_value('main', 'substitution_vars').split(', '):
        globalvars.SUBSTITUTION_MAP[v] = get_config_value('fs', v)
    for l in get_config_value('main', 'substitution_lists').split(', '):
        for v in get_config_value('fs', l).split(', '):
            varname = l.replace('_hier', '') + '_' + v
            globalvars.SUBSTITUTION_MAP[varname] = get_config_value('fs', varname)
    helpers.verbose_output("ok\n")

def ensure_fs_hierarchy(hier):
    for d in get_config_value('fs', hier + '_hier').split(', '):
        directory = get_config_value('fs', hier + '_' + d)
        helpers.verbose_output("Filesystem: Ensuring directory \"" + directory + "\" exists... ")
        if not os.path.isdir(directory):
            try:
                os.makedirs(directory)
            except OSError as e:
                helpers.die("\nFilesystem error: Could not create directory \"" + directory + "\"! Exiting.")
        helpers.verbose_output("ok\n")

def ensure_fs():
    ensure_fs_hierarchy('rjail')
    ensure_fs_hierarchy('rbuild')
    print("Filesystem: Hierarchy is in place.")

def is_package_present(package):
    for f in get_config_value('mini_manifest', package).split(', '):
        if not os.path.isfile(f):
            return False
    return True

def detect_packages():
    packages_present = []
    packages_missing = []
    value = get_config_value('main', 'packages').split(', ')
    if isinstance(value, list):
        for p in get_config_value('main', 'packages').split(', '):
            if is_package_present(p):
                packages_present.append(p)
            else:
                packages_missing.append(p)
    else:
        if is_package_present(value):
            packages_present.append(value)
        else:
            packages_missing.append(value)
    return(packages_present, packages_missing)

def print_info():
    print("\nInformation summary:\n--------------------------------------")
    print("OSNAME: " + OSNAME)
    print("OSVERSION: " + OSVERSION)
    print("OSRELEASE: " + OSRELEASE)
    print("OSMAJOR: " + OSMAJOR)
    print("OSARCH: " + OSARCH)
    print("STDARCH: " + STDARCH)
    print("TARGET_TRIPLE: " + TGT_TRIPLE)
    print("--------------------------------------\n")
    print(str(len(packages_present)) + " packages present:")
    for p in packages_present:
        print(p + ' ', end='')
    print("\n" + str(len(packages_missing)) + " packages missing:")
    for p in packages_missing:
        print(p + ' ', end='')

def fetch_file(uri, directory, filename):
    print("Fetching \"" + filename + "\"... ", end='', flush=True)
    try:
        urlretrieve(uri, directory + "/" + filename)
    except IOError as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            print("Error: Could not verify TLS certificate for \"" + uri + "\"! ", end='', flush=True)
            helpers.die("(Do you have the certs package installed?)")
        else:
            print(e)
            helpers.die("Unknown error!")
    except Exception as e:
        raise
    print("ok")

def get_file_hash(uri):
    md5_hash = hashlib.md5()
    with open(uri, "rb") as f:
        for block in iter(lambda: f.read(4096),b""):
            md5_hash.update(block)
    return(md5_hash.hexdigest())

def get_filename(section, package):
    if not package in config[section]:
        helpers.die("Error: Could not find key for \"" + package + "\" in section \"" + section + "\"! Exiting.")
    uri = get_config_value(section, package)
    return(os.path.basename(uri))

def get_archive_extension(filename):
    for e in get_config_value('decompress', 'file_types').split(', '):
        if filename.endswith(e) == True:
            return(e)
    helpers.die("Unsupported archive type for file \"" + filename + "\"! Exiting.")

def get_tarball_uri(package):
    filename = get_filename('distfiles', package)
    extension = get_archive_extension(filename)
    tarball = filename.rstrip(extension) + ".tar"
    return(globalvars.SUBSTITUTION_MAP['rbuild_dist_uncomp_dir'] + '/' + tarball)

def remove_file_or_dir(uri):
    if os.path.isfile(uri):
        try:
            os.remove(uri)
        except OSError as e:
            helpers.die("Error deleting file \"" + uri + "\"! Exiting.")
    elif os.path.isdir(uri):
        try:
            shutil.rmtree(uri)
        except OSError as e:
            helpers.die("Error deleting directory \"" + uri + "\"! Exiting.")
    else:
        helpers.die("Filesystem object \"" + uri + "\" is neither an ordinary file nor a directory. Refusing to delete! Exiting.")

def get_distfile_checksum(hashtype, package):
    if hashtype != "md5" and hashtype != "umd5":
        helpers.die("Unknown distfile hash type \"" + hashtype + "\"!") 
    if package in config["distfile_" + hashtype]:
        return(get_config_value("distfile_" + hashtype, package))
    return(None)

def ensure_distfile(mode, package):
    if mode == "compressed":
        distdir = globalvars.SUBSTITUTION_MAP['rbuild_dist_comp_dir']
        filename = get_filename('distfiles', package)
        hashtype = "md5"
    elif mode == "uncompressed":
        distdir = globalvars.SUBSTITUTION_MAP['rbuild_dist_uncomp_dir']
        filename = os.path.basename(get_tarball_uri(package))
        hashtype = "umd5"
    else:
        helpers.die("Invalid ensure_distfile mode \"" + mode + "\"! Aborting...")
    absolute_path = distdir + '/' + filename

    if not os.path.isfile(absolute_path):
        if mode == "compressed":
            fetch_file(get_config_value('distfiles', package), distdir, filename)
        else:
            decompress_file(globalvars.SUBSTITUTION_MAP['rbuild_dist_comp_dir'], get_filename('distfiles', package), distdir)

    checksum = get_distfile_checksum(hashtype, package)
    helpers.verbose_output("Checksum for \"" + package + "\": Comparing for " + mode + " distfile... ")
    if checksum == None:
        helpers.verbose_output("skipping (not available)\n")
    else:
        if get_file_hash(absolute_path) == checksum:
            helpers.verbose_output("ok (matches)\n")
        else:
            if mode == "compressed":
                helpers.verbose_output("Mismatch! Fetching again...\n")
                remove_file_or_dir(absolute_path)
                fetch_file(get_config_value('distfiles', package), globalvars.SUBSTITUTION_MAP['rbuild_dist_comp_dir'], filename)
                helpers.verbose_output("Comparing checksums once more... ")
                if get_file_hash(absolute_path) == checksum:
                    helpers.verbose_output("ok (matches)\n")
                else:
                    helpers.die("Mismatch again! Bailing out...")
            else:
                helpers.verbose_output("Mismatch! Extracting again...\n")
                helpers.die("Extract again!")

def do_shell_cmd(cmd, cwd, env):
    p = subprocess.Popen(cmd, cwd=cwd, env=env, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # ~ p = subprocess.run(args=cmd, cwd=cwd, env=env, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        helpers.die("\nError: Shell execution failed!\nstdout: " + stdout.decode() + "\nstderr: " + stderr.decode())
    return(p.returncode)

def assert_binary_available(binary):
    if not binary in get_config_value('main', 'external_binaries').split(', '):
        program = get_config_value("fs", "tgt_prefix") + "/bin/" + binary
        if not os.path.isfile(program):
            helpers.die("Cannot decompress \"" + extenstion + "\" archives before the package is built (check package order)! Exiting.")

def decompress_file(srcdir, filename, tgt_dir):
    helpers.verbose_output("Decompressing \"" + filename + "\"... ")
    extension = get_archive_extension(filename)
    
    if extension.startswith("tar"):
        binary = get_config_value("decompress", extension[4:] + "_bin")
    elif extension.startswith("t"):
        binary = get_config_value("decompress", extension[2:] + "_bin")
    else:
        helpers.die("Error: Unhandled archive \"" + extension + "\"! Exiting.")
    assert_binary_available(binary)
    
    generic_cmds = get_config_value("decompress", "decompress_cmd").split(', ')
    for c in generic_cmds:
        cmd = c.replace('%INFILE%', srcdir + '/' + filename).replace('%TGT_DIR%', tgt_dir).replace('%BINARY%', binary).replace('%FILENAME%', filename)
        # ~ r = do_shell_cmd(cmd, globalvars.SUBSTITUTION_MAP['rbuild_dist_uncomp_dir'], None)
        r = do_shell_cmd(cmd, tgt_dir, None)
        if r != 0:
            helpers.die("\nError: Could not decompress archive \"" + infile + "\"!")
    helpers.verbose_output("ok\n")

def extract_tarball(package):
    print("Extracting \"" + os.path.basename(get_tarball_uri(package)) + "\"... ", end='', flush=True)
    cmd = "tar -C " + globalvars.SUBSTITUTION_MAP['rbuild_const_dir'] + " -xf " + get_tarball_uri(package)
    r = do_shell_cmd(cmd, None, None)
    if r != 0:
        helpers.die("\nError: Could not extract tarball \"" + os.path.basename(get_tarball_uri(package)) + "\"! Exiting.")
    print("ok")

def ensure_extrafiles_present(package):
    extradir = globalvars.SUBSTITUTION_MAP['rbuild_extra_dir'] + '/' + package
    extrafiles = get_config_value('extrafiles', package).split(", ")
    md5s = None
    if package + "_md5" in config['extrafiles']:
        md5s = get_config_value('extrafiles', package + "_md5").split(", ")
    helpers.verbose_output("Extra files: Ensuring directory \"" + extradir + "\" exists... ")
    if not os.path.isdir(extradir):
        try:
            os.makedirs(extradir)
        except OSError as e:
            helpers.die("\nPatches error: Could not create directory \"" + extradir + "\"! Exiting.")
    helpers.verbose_output("ok\n")
    
    i = 0
    for f in extrafiles:
        filename = os.path.basename(f)
        absolute_path = extradir + '/' + filename
        if not os.path.isfile(absolute_path):
            fetch_file(f, extradir, filename)
        helpers.verbose_output("Comparing checksums for extra file " + str(i) + "... ")
        if md5s == None:
            helpers.verbose_output("skipping (not available)\n")
        else:
            if get_file_hash(absolute_path) == md5s[i]:
                helpers.verbose_output("ok (matches)\n")
            else:
                helpers.verbose_output("Mismatch! Fetching again...\n")
                remove_file_or_dir(absolute_path)
                fetch_file(f, extradir, filename)
                helpers.verbose_output("Comparing checksums once more... ")
                if get_file_hash(absolute_path) == md5s[i]:
                    helpers.verbose_output("ok (matches)\n")
                else:
                    helpers.die("Mismatch again! Bailing out...")
        i = i + 1

def get_wrkdir(package):
    if package + "_name" in config['distfiles']:
        return(globalvars.SUBSTITUTION_MAP['rbuild_const_dir'] + '/' + get_config_value('distfiles', package + "_name"))
    elif package in config['distfiles']:
        return(globalvars.SUBSTITUTION_MAP['rbuild_const_dir'] + '/' + os.path.basename(get_tarball_uri(package).rstrip(".tar")))
    else:
        return(globalvars.SUBSTITUTION_MAP['rbuild_const_dir'] + '/' + package)

def ensure_clean_wrkdir(package):
    wrkdir = get_wrkdir(package)
    if os.path.exists(wrkdir):
        print("Old workdir found. Deleting... ", end='', flush=True)
        remove_file_or_dir(wrkdir)
        print("ok")
        
    if package in config['distfiles']:
        ensure_distfile("compressed", package)
        ensure_distfile("uncompressed", package)
        extract_tarball(package)
    
    if package in config['extrafiles']:
        if not os.path.exists(wrkdir):
            try:
                os.makedirs(wrkdir)
            except OSError as e:
                helpers.die("\nFilesystem error: Could not create directory \"" + directory + "\"! Exiting.")
        
        if package in config['extrafiles']:
            ensure_extrafiles_present(package)
            extradir = globalvars.SUBSTITUTION_MAP['rbuild_extra_dir'] + '/' + package
            extrafiles = get_config_value('extrafiles', package).split(", ")
            for f in extrafiles:
                absolute_path = extradir + '/' + os.path.basename(f)
                try:
                    shutil.copy(absolute_path, wrkdir)
                except IOError as e:
                    helpers.die("\nFilesystem error: Could not copy \"" + absolute_path + "\" to \"" + wrkdir + "\"! Exiting.")

def ensure_patchfiles_present(package):
    patches = get_config_value('patches', package).split(", ")
    md5s = None
    if package + "_md5" in config['patches']:
        md5s = get_config_value('patches', package + "_md5").split(", ")
    patchdir = globalvars.SUBSTITUTION_MAP['rbuild_patches_dir'] + '/' + package
    helpers.verbose_output("Patches: Ensuring directory \"" + patchdir + "\" exists... ")
    if not os.path.isdir(patchdir):
        try:
            os.makedirs(patchdir)
        except OSError as e:
            helpers.die("\nPatches error: Could not create directory \"" + patchdir + "\"! Exiting.")
    helpers.verbose_output("ok\n")
    i = 0
    
    for uri in patches:
        filename = os.path.basename(uri)
        absolute_path = patchdir + '/' + filename
        if not os.path.isfile(absolute_path):
            fetch_file(uri, patchdir, filename)
        helpers.verbose_output("Comparing checksums for patch " + str(i) + "... ")
        if md5s == None:
            helpers.verbose_output("skipping (not available)\n")
        else:
            if get_file_hash(absolute_path) == md5s[i]:
                helpers.verbose_output("ok (matches)\n")
            else:
                helpers.verbose_output("Mismatch! Fetching again...\n")
                remove_file_or_dir(absolute_path)
                fetch_file(uri, patchdir, filename)
                helpers.verbose_output("Comparing checksums once more... ")
                if get_file_hash(absolute_path) == md5s[i]:
                    helpers.verbose_output("ok (matches)\n")
                else:
                    helpers.die("Mismatch again! Bailing out...")
        i = i + 1

def prepare_env(env, package):
    environ = os.environ.copy()
    env_add = []
    if env in config['default']:
        for v in get_config_value('default', env).split(', '):
           if v.count('|') != 1:
                helpers.die("Error: Invalid default environment variable assignment \"" + v + "\"! Exiting.")
           env_add.append(v.split('|'))
    
    if package in config[env + '_env']:
        for v in get_config_value(env + '_env', package).split(', '):
            if v.count('|') != 1:
                helpers.die("Error: Invalid " + env + " environment variable assignment \"" + v + "\" for package \"" + package + "\"! Exiting.")
            env_add.append(v.split('|'))
    
    for e in env_add:
        environ[e[0]] = e[1]
    return(environ)

def reinplace(filename, string, repl):
    with open(filename) as f:
        s = f.read()

    with open(filename, 'w') as f:
        s = s.replace(string, "\"" + repl + "\"")
        f.write(s)

def prepare_bmake_patch():
    helpers.verbose_output("Adapting bmake patch to target system... ")
    for s in ["OSNAME", "OSVERSION", "OSRELEASE", "OSMAJOR", "OSARCH", "STDARCH"]:
        reinplace(globalvars.SUBSTITUTION_MAP['rbuild_patches_dir'] + "/bmake/patch-main.c", s, globals()[s])
    helpers.verbose_output("ok\n")

def prepare_uname_source():
    wrkdir = get_wrkdir("uname")
    helpers.verbose_output("Applying plattform info to fake uname... ")
    reinplace(wrkdir + "/uname.c.in", "\"@OPSYS@\"", OSNAME)
    reinplace(wrkdir + "/uname.c.in", "\"@ARCH@\"", OSARCH)
    reinplace(wrkdir + "/uname.c.in", "\"@PLATFORM@\"", STDARCH)
    reinplace(wrkdir + "/uname.c.in", "\"@RELEASE@\"", OSRELEASE + "-RAVEN")
    reinplace(wrkdir + "/uname.c.in", "\"@USERVER@\"", OSVERSION)
    reinplace(wrkdir + "/uname.c.in", "\"@OPSYS@ @RELEASE@ #0 Sat Jul 29 09:00:00 CDT 2017 root@octavia.unreal.systems:/usr/obj/usr/src/sys/GENERIC\"", OSNAME + " " + OSRELEASE + " #0 " + time.ctime() + " root@" + socket.getfqdn() + ":/usr/obj/usr/src/sys/GENERIC")
    reinplace(wrkdir + "/uname.c.in", "\"octavia.unreal.systems\"", socket.getfqdn())
    helpers.verbose_output("ok\n")

def patch_source(package):
    patches = get_config_value('patches', package).split(", ")
    patchdir = globalvars.SUBSTITUTION_MAP['rbuild_patches_dir'] + '/' + package
    i = 0
    for uri in patches:
        filename = os.path.basename(uri)
        absolute_path = patchdir + '/' + filename
        helpers.verbose_output("Patching source of " + package + ": Applying patch " + str(i) + "... ")
        cmd = "patch -i " + absolute_path
        r = do_shell_cmd(cmd, get_wrkdir(package), None)
        if r != 0:
            helpers.die("\nError applying patch \"" + absolute_path + "\"! Exiting.")
        helpers.verbose_output("ok\n")
        i = i + 1

def build_package(phase, package):
    if phase == "configure":
        activity = "Configuring"
        env = phase
    elif phase == "make":
        activity = "Building"
        env = phase
    elif phase == "install":
        activity = "Installing"
        env = "make"
    else:
        helpers.die("\nError: Unknown build phase \"" + phase + "\"! Exiting.")
    env = prepare_env(env, package)
    print(activity + " \"" + package + "\"... ", end='', flush=True)
    wrkdir = get_wrkdir(package)
    for cmd in get_config_value(phase + "_cmds", package).split(', '):
        r = do_shell_cmd(cmd, wrkdir, env)
        if r != 0:
            helpers.die("\nError: " + activity + " failed for package \"" + package + "\"! Exiting.")
    print("ok")

def build_missing():
    print()
    for p in packages_missing:
        ensure_clean_wrkdir(p)
        if p == "uname":
            prepare_uname_source()
        if p in config['patches']:
            ensure_patchfiles_present(p)
            if p == "bmake":
                prepare_bmake_patch()
            patch_source(p)
        if p in config['configure_cmds']:
            build_package('configure', p)
        if p in config['make_cmds']:
            build_package('make', p)
        build_package('install', p)

##########
 # Main #
##########

assert_conf_file_present()
config = configparser.ConfigParser()
config.read(globalvars.CONFNAME)
assert_config_valid()

OSNAME = get_osname()
if not OSNAME in globalvars.OPERATING_SYSTEMS_SUPPORTED:
    helpers.die("Unsupported OS: \"" + OSNAME + "\"!")
OSVERSION = get_os_version()
OSRELEASE = get_os_release()
OSMAJOR = get_os_major()
OSARCH = get_os_arch()
STDARCH = get_stdarch()
TGT_TRIPLE = assemble_triple()
print("System: Set for " + TGT_TRIPLE + ".")

populate_substitution_map()
assert_external_binaries_available()
ensure_fs()
packages_present, packages_missing = detect_packages()
print_info()

if len(packages_missing) > 0:
    a = 0
    while (a != "N" and a != "Y"):
        a = input("\n\nBuild missing packages now? (Y/N) ").upper()
    if (a == "N"):
        exit(0)
build_missing()
print("All done!")

#!/usr/local/bin/python3.7

#############
 # Imports #
#############

import globalvars
import modules.conf as conf
import modules.helpers as helpers
import modules.platform as platform
import modules.subst as subst
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

def populate_substitution_map():
    globalvars.SUBSTITUTION_MAP
    helpers.verbose_output("Internal: Populating substitution map... ")
    for v in conf.get_config_value('main', 'substitution_vars').split(', '):
        globalvars.SUBSTITUTION_MAP[v] = conf.get_config_value('fs', v)
    for l in conf.get_config_value('main', 'substitution_lists').split(', '):
        for v in conf.get_config_value('fs', l).split(', '):
            varname = l.replace('_hier', '') + '_' + v
            globalvars.SUBSTITUTION_MAP[varname] = conf.get_config_value('fs', varname)
    helpers.verbose_output("ok\n")

def is_package_present(package):
    for f in conf.get_config_value('mini_manifest', package).split(', '):
        if not os.path.isfile(f):
            return False
    return True

def detect_packages():
    packages_present = []
    packages_missing = []
    value = conf.get_config_value('main', 'packages').split(', ')
    if isinstance(value, list):
        for p in conf.get_config_value('main', 'packages').split(', '):
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
    print("OSNAME: " + globalvars.OSNAME)
    print("OSVERSION: " + globalvars.OSVERSION)
    print("OSRELEASE: " + globalvars.OSRELEASE)
    print("OSMAJOR: " + globalvars.OSMAJOR)
    print("OSARCH: " + globalvars.OSARCH)
    print("STDARCH: " + globalvars.STDARCH)
    print("TARGET_TRIPLE: " + globalvars.TGT_TRIPLE)
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
    if not package in conf.config[section]:
        helpers.die("Error: Could not find key for \"" + package + "\" in section \"" + section + "\"! Exiting.")
    uri = conf.get_config_value(section, package)
    return(os.path.basename(uri))

def get_archive_extension(filename):
    for e in conf.get_config_value('decompress', 'file_types').split(', '):
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
    if package in conf.config["distfile_" + hashtype]:
        return(conf.get_config_value("distfile_" + hashtype, package))
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
            fetch_file(conf.get_config_value('distfiles', package), distdir, filename)
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
                fetch_file(conf.get_config_value('distfiles', package), globalvars.SUBSTITUTION_MAP['rbuild_dist_comp_dir'], filename)
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
    if not binary in conf.get_config_value('main', 'external_binaries').split(', '):
        program = conf.get_config_value("fs", "tgt_prefix") + "/bin/" + binary
        if not os.path.isfile(program):
            helpers.die("Cannot decompress \"" + extenstion + "\" archives before the package is built (check package order)! Exiting.")

def decompress_file(srcdir, filename, tgt_dir):
    helpers.verbose_output("Decompressing \"" + filename + "\"... ")
    extension = get_archive_extension(filename)
    
    if extension.startswith("tar"):
        binary = conf.get_config_value("decompress", extension[4:] + "_bin")
    elif extension.startswith("t"):
        binary = conf.get_config_value("decompress", extension[2:] + "_bin")
    else:
        helpers.die("Error: Unhandled archive \"" + extension + "\"! Exiting.")
    assert_binary_available(binary)
    
    generic_cmds = conf.get_config_value("decompress", "decompress_cmd").split(', ')
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
    extrafiles = conf.get_config_value('extrafiles', package).split(", ")
    md5s = None
    if package + "_md5" in conf.config['extrafiles']:
        md5s = conf.get_config_value('extrafiles', package + "_md5").split(", ")
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
    if package + "_name" in conf.config['distfiles']:
        return(globalvars.SUBSTITUTION_MAP['rbuild_const_dir'] + '/' + conf.get_config_value('distfiles', package + "_name"))
    elif package in conf.config['distfiles']:
        return(globalvars.SUBSTITUTION_MAP['rbuild_const_dir'] + '/' + os.path.basename(get_tarball_uri(package).rstrip(".tar")))
    else:
        return(globalvars.SUBSTITUTION_MAP['rbuild_const_dir'] + '/' + package)

def ensure_clean_wrkdir(package):
    wrkdir = get_wrkdir(package)
    if os.path.exists(wrkdir):
        print("Old workdir found. Deleting... ", end='', flush=True)
        remove_file_or_dir(wrkdir)
        print("ok")
        
    if package in conf.config['distfiles']:
        ensure_distfile("compressed", package)
        ensure_distfile("uncompressed", package)
        extract_tarball(package)
    
    if package in conf.config['extrafiles']:
        if not os.path.exists(wrkdir):
            try:
                os.makedirs(wrkdir)
            except OSError as e:
                helpers.die("\nFilesystem error: Could not create directory \"" + directory + "\"! Exiting.")
        
        if package in conf.config['extrafiles']:
            ensure_extrafiles_present(package)
            extradir = globalvars.SUBSTITUTION_MAP['rbuild_extra_dir'] + '/' + package
            extrafiles = conf.get_config_value('extrafiles', package).split(", ")
            for f in extrafiles:
                absolute_path = extradir + '/' + os.path.basename(f)
                try:
                    shutil.copy(absolute_path, wrkdir)
                except IOError as e:
                    helpers.die("\nFilesystem error: Could not copy \"" + absolute_path + "\" to \"" + wrkdir + "\"! Exiting.")

def ensure_patchfiles_present(package):
    patches = conf.get_config_value('patches', package).split(", ")
    md5s = None
    if package + "_md5" in conf.config['patches']:
        md5s = conf.get_config_value('patches', package + "_md5").split(", ")
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
    if env in conf.config['default']:
        for v in conf.get_config_value('default', env).split(', '):
           if v.count('|') != 1:
                helpers.die("Error: Invalid default environment variable assignment \"" + v + "\"! Exiting.")
           env_add.append(v.split('|'))
    
    if package in conf.config[env + '_env']:
        for v in conf.get_config_value(env + '_env', package).split(', '):
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
        reinplace(globalvars.SUBSTITUTION_MAP['rbuild_patches_dir'] + "/bmake/patch-main.c", s, eval("globalvars." + s))
    helpers.verbose_output("ok\n")

def prepare_uname_source():
    wrkdir = get_wrkdir("uname")
    helpers.verbose_output("Applying plattform info to fake uname... ")
    reinplace(wrkdir + "/uname.c.in", "\"@OPSYS@\"", globalvars.OSNAME)
    reinplace(wrkdir + "/uname.c.in", "\"@ARCH@\"", globalvars.OSARCH)
    reinplace(wrkdir + "/uname.c.in", "\"@PLATFORM@\"", globalvars.STDARCH)
    reinplace(wrkdir + "/uname.c.in", "\"@RELEASE@\"", globalvars.OSRELEASE + "-RAVEN")
    reinplace(wrkdir + "/uname.c.in", "\"@USERVER@\"", globalvars.OSVERSION)
    reinplace(wrkdir + "/uname.c.in", "\"@OPSYS@ @RELEASE@ #0 Sat Jul 29 09:00:00 CDT 2017 root@octavia.unreal.systems:/usr/obj/usr/src/sys/GENERIC\"", globalvars.OSNAME + " " + globalvars.OSRELEASE + " #0 " + time.ctime() + " root@" + socket.getfqdn() + ":/usr/obj/usr/src/sys/GENERIC")
    reinplace(wrkdir + "/uname.c.in", "\"octavia.unreal.systems\"", socket.getfqdn())
    helpers.verbose_output("ok\n")

def patch_source(package):
    patches = conf.get_config_value('patches', package).split(", ")
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
    for cmd in conf.get_config_value(phase + "_cmds", package).split(', '):
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
        if p in conf.config['patches']:
            ensure_patchfiles_present(p)
            if p == "bmake":
                prepare_bmake_patch()
            patch_source(p)
        if p in conf.config['configure_cmds']:
            build_package('configure', p)
        if p in conf.config['make_cmds']:
            build_package('make', p)
        build_package('install', p)

##########
 # Main #
##########

conf.assert_conf_file_present()
conf.config = configparser.ConfigParser()
conf.config.read(globalvars.CONFNAME)
conf.assert_config_valid()

globalvars.OSNAME = platform.get_osname()
if not globalvars.OSNAME in globalvars.OPERATING_SYSTEMS_SUPPORTED:
    helpers.die("Unsupported OS: \"" + globalvars.OSNAME + "\"!")
globalvars.OSVERSION = platform.get_os_version()
globalvars.OSRELEASE = platform.get_os_release()
globalvars.OSMAJOR = platform.get_os_major()
globalvars.OSARCH = platform.get_os_arch()
globalvars.STDARCH = platform.get_stdarch()
globalvars.TGT_TRIPLE = platform.assemble_triple()
print("System: Set for " + globalvars.TGT_TRIPLE + ".")

populate_substitution_map()
helpers.assert_external_binaries_available()
helpers.ensure_fs()
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

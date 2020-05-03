#!/usr/local/bin/python3.7

#############
 # Imports #
#############

import globalvars
import modules.conf as conf
import modules.misc as misc
import modules.platform as platform
import modules.subst as subst
import configparser
import os
import re
import socket
import subprocess
import time

###############
 # Functions #
###############

def ensure_fs():
    misc.ensure_fs_hierarchy('rjail')
    misc.ensure_fs_hierarchy('rbuild')
    print("Filesystem: Hierarchy is in place.")

def detect_packages():
    packages_present = []
    packages_missing = []
    value = conf.get_config_value('main', 'packages').split(', ')
    if isinstance(value, list):
        for p in conf.get_config_value('main', 'packages').split(', '):
            if misc.is_package_present(p):
                packages_present.append(p)
            else:
                packages_missing.append(p)
    else:
        if misc.is_package_present(value):
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

def ensure_distfile(mode, package):
    if mode == "compressed":
        distdir = globalvars.SUBSTITUTION_MAP['rbuild_dist_comp_dir']
        filename = misc.get_filename('distfiles', package)
        hashtype = "md5"
    elif mode == "uncompressed":
        distdir = globalvars.SUBSTITUTION_MAP['rbuild_dist_uncomp_dir']
        filename = os.path.basename(misc.get_tarball_uri(package))
        hashtype = "umd5"
    else:
        misc.die("Invalid ensure_distfile mode \"" + mode + "\"! Aborting...")
    absolute_path = distdir + '/' + filename

    if not os.path.isfile(absolute_path):
        if mode == "compressed":
            misc.fetch_file(conf.get_config_value('distfiles', package), distdir, filename)
        else:
            decompress_file(globalvars.SUBSTITUTION_MAP['rbuild_dist_comp_dir'], misc.get_filename('distfiles', package), distdir)

    checksum = misc.get_distfile_checksum(hashtype, package)
    misc.verbose_output("Checksum for \"" + package + "\": Comparing for " + mode + " distfile... ")
    if checksum == None:
        misc.verbose_output("skipping (not available)\n")
    else:
        if misc.get_file_hash(absolute_path) == checksum:
            misc.verbose_output("ok (matches)\n")
        else:
            if mode == "compressed":
                misc.verbose_output("Mismatch! Fetching again...\n")
                misc.remove_file_or_dir(absolute_path)
                misc.fetch_file(conf.get_config_value('distfiles', package), globalvars.SUBSTITUTION_MAP['rbuild_dist_comp_dir'], filename)
                misc.verbose_output("Comparing checksums once more... ")
                if misc.get_file_hash(absolute_path) == checksum:
                    misc.verbose_output("ok (matches)\n")
                else:
                    misc.die("Mismatch again! Bailing out...")
            else:
                misc.verbose_output("Mismatch! Extracting again...\n")
                misc.die("Extract again!")

def do_shell_cmd(cmd, cwd, env):
    p = subprocess.Popen(cmd, cwd=cwd, env=env, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # ~ p = subprocess.run(args=cmd, cwd=cwd, env=env, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        misc.die("\nError: Shell execution failed!\nstdout: " + stdout.decode() + "\nstderr: " + stderr.decode())
    return(p.returncode)

def assert_binary_available(binary):
    if not binary in conf.get_config_value('main', 'external_binaries').split(', '):
        program = conf.get_config_value("fs", "tgt_prefix") + "/bin/" + binary
        if not os.path.isfile(program):
            misc.die("Cannot decompress \"" + extenstion + "\" archives before the package is built (check package order)! Exiting.")

def decompress_file(srcdir, filename, tgt_dir):
    misc.verbose_output("Decompressing \"" + filename + "\"... ")
    extension = misc.get_archive_extension(filename)
    
    if extension.startswith("tar"):
        binary = conf.get_config_value("decompress", extension[4:] + "_bin")
    elif extension.startswith("t"):
        binary = conf.get_config_value("decompress", extension[2:] + "_bin")
    else:
        misc.die("Error: Unhandled archive \"" + extension + "\"! Exiting.")
    assert_binary_available(binary)
    
    generic_cmds = conf.get_config_value("decompress", "decompress_cmd").split(', ')
    for c in generic_cmds:
        cmd = c.replace('%INFILE%', srcdir + '/' + filename).replace('%TGT_DIR%', tgt_dir).replace('%BINARY%', binary).replace('%FILENAME%', filename)
        # ~ r = do_shell_cmd(cmd, globalvars.SUBSTITUTION_MAP['rbuild_dist_uncomp_dir'], None)
        r = do_shell_cmd(cmd, tgt_dir, None)
        if r != 0:
            misc.die("\nError: Could not decompress archive \"" + infile + "\"!")
    misc.verbose_output("ok\n")

def extract_tarball(package):
    print("Extracting \"" + os.path.basename(misc.get_tarball_uri(package)) + "\"... ", end='', flush=True)
    cmd = "tar -C " + globalvars.SUBSTITUTION_MAP['rbuild_const_dir'] + " -xf " + misc.get_tarball_uri(package)
    r = do_shell_cmd(cmd, None, None)
    if r != 0:
        misc.die("\nError: Could not extract tarball \"" + os.path.basename(misc.get_tarball_uri(package)) + "\"! Exiting.")
    print("ok")

def ensure_extrafiles_present(package):
    extradir = globalvars.SUBSTITUTION_MAP['rbuild_extra_dir'] + '/' + package
    extrafiles = conf.get_config_value('extrafiles', package).split(", ")
    md5s = None
    if package + "_md5" in conf.config['extrafiles']:
        md5s = conf.get_config_value('extrafiles', package + "_md5").split(", ")
    misc.verbose_output("Extra files: Ensuring directory \"" + extradir + "\" exists... ")
    if not os.path.isdir(extradir):
        try:
            os.makedirs(extradir)
        except OSError as e:
            misc.die("\nPatches error: Could not create directory \"" + extradir + "\"! Exiting.")
    misc.verbose_output("ok\n")
    
    i = 0
    for f in extrafiles:
        filename = os.path.basename(f)
        absolute_path = extradir + '/' + filename
        if not os.path.isfile(absolute_path):
            misc.fetch_file(f, extradir, filename)
        misc.verbose_output("Comparing checksums for extra file " + str(i) + "... ")
        if md5s == None:
            misc.verbose_output("skipping (not available)\n")
        else:
            if misc.get_file_hash(absolute_path) == md5s[i]:
                misc.verbose_output("ok (matches)\n")
            else:
                misc.verbose_output("Mismatch! Fetching again...\n")
                misc.remove_file_or_dir(absolute_path)
                misc.fetch_file(f, extradir, filename)
                misc.verbose_output("Comparing checksums once more... ")
                if misc.get_file_hash(absolute_path) == md5s[i]:
                    misc.verbose_output("ok (matches)\n")
                else:
                    misc.die("Mismatch again! Bailing out...")
        i = i + 1

def get_wrkdir(package):
    if package + "_name" in conf.config['distfiles']:
        return(globalvars.SUBSTITUTION_MAP['rbuild_const_dir'] + '/' + conf.get_config_value('distfiles', package + "_name"))
    elif package in conf.config['distfiles']:
        return(globalvars.SUBSTITUTION_MAP['rbuild_const_dir'] + '/' + os.path.basename(misc.get_tarball_uri(package).rstrip(".tar")))
    else:
        return(globalvars.SUBSTITUTION_MAP['rbuild_const_dir'] + '/' + package)

def ensure_clean_wrkdir(package):
    wrkdir = get_wrkdir(package)
    if os.path.exists(wrkdir):
        print("Old workdir found. Deleting... ", end='', flush=True)
        misc.remove_file_or_dir(wrkdir)
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
                misc.die("\nFilesystem error: Could not create directory \"" + directory + "\"! Exiting.")
        
        if package in conf.config['extrafiles']:
            ensure_extrafiles_present(package)
            extradir = globalvars.SUBSTITUTION_MAP['rbuild_extra_dir'] + '/' + package
            extrafiles = conf.get_config_value('extrafiles', package).split(", ")
            for f in extrafiles:
                absolute_path = extradir + '/' + os.path.basename(f)
                try:
                    shutil.copy(absolute_path, wrkdir)
                except IOError as e:
                    misc.die("\nFilesystem error: Could not copy \"" + absolute_path + "\" to \"" + wrkdir + "\"! Exiting.")

def ensure_patchfiles_present(package):
    patches = conf.get_config_value('patches', package).split(", ")
    md5s = None
    if package + "_md5" in conf.config['patches']:
        md5s = conf.get_config_value('patches', package + "_md5").split(", ")
    patchdir = globalvars.SUBSTITUTION_MAP['rbuild_patches_dir'] + '/' + package
    misc.verbose_output("Patches: Ensuring directory \"" + patchdir + "\" exists... ")
    if not os.path.isdir(patchdir):
        try:
            os.makedirs(patchdir)
        except OSError as e:
            misc.die("\nPatches error: Could not create directory \"" + patchdir + "\"! Exiting.")
    misc.verbose_output("ok\n")
    i = 0
    
    for uri in patches:
        filename = os.path.basename(uri)
        absolute_path = patchdir + '/' + filename
        if not os.path.isfile(absolute_path):
            misc.fetch_file(uri, patchdir, filename)
        misc.verbose_output("Comparing checksums for patch " + str(i) + "... ")
        if md5s == None:
            misc.verbose_output("skipping (not available)\n")
        else:
            if misc.get_file_hash(absolute_path) == md5s[i]:
                misc.verbose_output("ok (matches)\n")
            else:
                misc.verbose_output("Mismatch! Fetching again...\n")
                misc.remove_file_or_dir(absolute_path)
                misc.fetch_file(uri, patchdir, filename)
                misc.verbose_output("Comparing checksums once more... ")
                if misc.get_file_hash(absolute_path) == md5s[i]:
                    misc.verbose_output("ok (matches)\n")
                else:
                    misc.die("Mismatch again! Bailing out...")
        i = i + 1

def prepare_env(env, package):
    environ = os.environ.copy()
    env_add = []
    if env in conf.config['default']:
        for v in conf.get_config_value('default', env).split(', '):
           if v.count('|') != 1:
                misc.die("Error: Invalid default environment variable assignment \"" + v + "\"! Exiting.")
           env_add.append(v.split('|'))
    
    if package in conf.config[env + '_env']:
        for v in conf.get_config_value(env + '_env', package).split(', '):
            if v.count('|') != 1:
                misc.die("Error: Invalid " + env + " environment variable assignment \"" + v + "\" for package \"" + package + "\"! Exiting.")
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
    misc.verbose_output("Adapting bmake patch to target system... ")
    for s in ["OSNAME", "OSVERSION", "OSRELEASE", "OSMAJOR", "OSARCH", "STDARCH"]:
        reinplace(globalvars.SUBSTITUTION_MAP['rbuild_patches_dir'] + "/bmake/patch-main.c", s, eval("globalvars." + s))
    misc.verbose_output("ok\n")

def prepare_uname_source():
    wrkdir = get_wrkdir("uname")
    misc.verbose_output("Applying plattform info to fake uname... ")
    reinplace(wrkdir + "/uname.c.in", "\"@OPSYS@\"", globalvars.OSNAME)
    reinplace(wrkdir + "/uname.c.in", "\"@ARCH@\"", globalvars.OSARCH)
    reinplace(wrkdir + "/uname.c.in", "\"@PLATFORM@\"", globalvars.STDARCH)
    reinplace(wrkdir + "/uname.c.in", "\"@RELEASE@\"", globalvars.OSRELEASE + "-RAVEN")
    reinplace(wrkdir + "/uname.c.in", "\"@USERVER@\"", globalvars.OSVERSION)
    reinplace(wrkdir + "/uname.c.in", "\"@OPSYS@ @RELEASE@ #0 Sat Jul 29 09:00:00 CDT 2017 root@octavia.unreal.systems:/usr/obj/usr/src/sys/GENERIC\"", globalvars.OSNAME + " " + globalvars.OSRELEASE + " #0 " + time.ctime() + " root@" + socket.getfqdn() + ":/usr/obj/usr/src/sys/GENERIC")
    reinplace(wrkdir + "/uname.c.in", "\"octavia.unreal.systems\"", socket.getfqdn())
    misc.verbose_output("ok\n")

def patch_source(package):
    patches = conf.get_config_value('patches', package).split(", ")
    patchdir = globalvars.SUBSTITUTION_MAP['rbuild_patches_dir'] + '/' + package
    i = 0
    for uri in patches:
        filename = os.path.basename(uri)
        absolute_path = patchdir + '/' + filename
        misc.verbose_output("Patching source of " + package + ": Applying patch " + str(i) + "... ")
        cmd = "patch -i " + absolute_path
        r = do_shell_cmd(cmd, get_wrkdir(package), None)
        if r != 0:
            misc.die("\nError applying patch \"" + absolute_path + "\"! Exiting.")
        misc.verbose_output("ok\n")
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
        misc.die("\nError: Unknown build phase \"" + phase + "\"! Exiting.")
    env = prepare_env(env, package)
    print(activity + " \"" + package + "\"... ", end='', flush=True)
    wrkdir = get_wrkdir(package)
    for cmd in conf.get_config_value(phase + "_cmds", package).split(', '):
        r = do_shell_cmd(cmd, wrkdir, env)
        if r != 0:
            misc.die("\nError: " + activity + " failed for package \"" + package + "\"! Exiting.")
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
    misc.die("Unsupported OS: \"" + globalvars.OSNAME + "\"!")
globalvars.OSVERSION = platform.get_os_version()
globalvars.OSRELEASE = platform.get_os_release()
globalvars.OSMAJOR = platform.get_os_major()
globalvars.OSARCH = platform.get_os_arch()
globalvars.STDARCH = platform.get_stdarch()
globalvars.TGT_TRIPLE = platform.assemble_triple()
print("System: Set for " + globalvars.TGT_TRIPLE + ".")

subst.populate_substitution_map()
misc.assert_external_binaries_available()
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

#############
 # Imports #
#############

import globalvars
import modules.conf as conf
import hashlib
import os
import shutil
import subprocess
from urllib.request import urlretrieve

###############
 # Functions #
###############

def die(msg):
    print(msg)
    exit(1)

def verbose_output(string):
    if globalvars.VERBOSE:
        print(string, end="", flush=True)

def get_cmd_output(cmd, params):
    p = subprocess.Popen(cmd + " " + params, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.readlines()[0].strip().decode()

def assert_external_binaries_available():
    for b in conf.get_config_value('main', 'external_binaries').split(', '):
        verbose_output("Programs: Checking if \"" + b + "\" is available... ")
        p = subprocess.Popen('command -v ' + b, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if p.stdout.readlines() == []:
            die("\nError: \"" + b + "\" is not available on this system (or not in PATH)! Exiting.")
        verbose_output("ok\n")
    print("Programs: All required external programs are available.")

def ensure_fs_hierarchy(hier):
    for d in conf.get_config_value('fs', hier + '_hier').split(', '):
        directory = conf.get_config_value('fs', hier + '_' + d)
        verbose_output("Filesystem: Ensuring directory \"" + directory + "\" exists... ")
        if not os.path.isdir(directory):
            try:
                os.makedirs(directory)
            except OSError as e:
                die("\nFilesystem error: Could not create directory \"" + directory + "\"! Exiting.")
        verbose_output("ok\n")

def is_package_present(package):
    for f in conf.get_config_value('mini_manifest', package).split(', '):
        if not os.path.isfile(f):
            return False
    return True

def fetch_file(uri, directory, filename):
    print("Fetching \"" + filename + "\"... ", end='', flush=True)
    try:
        urlretrieve(uri, directory + "/" + filename)
    except IOError as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            print("Error: Could not verify TLS certificate for \"" + uri + "\"! ", end='', flush=True)
            die("(Do you have the certs package installed?)")
        else:
            print(e)
            die("Unknown error!")
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
        die("Error: Could not find key for \"" + package + "\" in section \"" + section + "\"! Exiting.")
    uri = conf.get_config_value(section, package)
    return(os.path.basename(uri))

def get_archive_extension(filename):
    for e in conf.get_config_value('decompress', 'file_types').split(', '):
        if filename.endswith(e) == True:
            return(e)
    die("Unsupported archive type for file \"" + filename + "\"! Exiting.")

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
            die("Error deleting file \"" + uri + "\"! Exiting.")
    elif os.path.isdir(uri):
        try:
            shutil.rmtree(uri)
        except OSError as e:
            die("Error deleting directory \"" + uri + "\"! Exiting.")
    else:
        die("Filesystem object \"" + uri + "\" is neither an ordinary file nor a directory. Refusing to delete! Exiting.")

def get_distfile_checksum(hashtype, package):
    if hashtype != "md5" and hashtype != "umd5":
        die("Unknown distfile hash type \"" + hashtype + "\"!") 
    if package in conf.config["distfile_" + hashtype]:
        return(conf.get_config_value("distfile_" + hashtype, package))
    return(None)

def main():
    print("This module is meant to be used with MiniRaven and not really useful on it's own.")
    exit(0)

##########
 # Main #
##########

if __name__ == "__main__":
    main()

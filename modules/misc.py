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

def do_shell_cmd(cmd, cwd, env):
    p = subprocess.Popen(cmd, cwd=cwd, env=env, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        die("\nError: Shell execution failed!\nstdout: " + stdout.decode() + "\nstderr: " + stderr.decode())
    return(p.returncode)

def assert_archiver_available(binary):
    if not binary in conf.get_config_value('main', 'external_binaries').split(', '):
        program = conf.get_config_value("fs", "tgt_prefix") + "/bin/" + binary
        if not os.path.isfile(program):
            die("Cannot decompress \"" + extenstion + "\" archives before the package is built (check package order)! Exiting.")

def decompress_file(srcdir, filename, tgt_dir):
    verbose_output("Decompressing \"" + filename + "\"... ")
    extension = get_archive_extension(filename)
    
    if extension.startswith("tar"):
        binary = conf.get_config_value("decompress", extension[4:] + "_bin")
    elif extension.startswith("t"):
        binary = conf.get_config_value("decompress", extension[2:] + "_bin")
    else:
        die("Error: Unhandled archive \"" + extension + "\"! Exiting.")
    assert_archiver_available(binary)
    
    generic_cmds = conf.get_config_value("decompress", "decompress_cmd").split(', ')
    for c in generic_cmds:
        cmd = c.replace('%INFILE%', srcdir + '/' + filename).replace('%TGT_DIR%', tgt_dir).replace('%BINARY%', binary).replace('%FILENAME%', filename)
        r = do_shell_cmd(cmd, tgt_dir, None)
        if r != 0:
            die("\nError: Could not decompress archive \"" + infile + "\"!")
    verbose_output("ok\n")

def extract_tarball(package):
    print("Extracting \"" + os.path.basename(get_tarball_uri(package)) + "\"... ", end='', flush=True)
    cmd = "tar -C " + globalvars.SUBSTITUTION_MAP['rbuild_const_dir'] + " -xf " + get_tarball_uri(package)
    r = do_shell_cmd(cmd, None, None)
    if r != 0:
        die("\nError: Could not extract tarball \"" + os.path.basename(get_tarball_uri(package)) + "\"! Exiting.")
    print("ok")

def get_wrkdir(package):
    if package + "_name" in conf.config['distfiles']:
        return(globalvars.SUBSTITUTION_MAP['rbuild_const_dir'] + '/' + conf.get_config_value('distfiles', package + "_name"))
    elif package in conf.config['distfiles']:
        return(globalvars.SUBSTITUTION_MAP['rbuild_const_dir'] + '/' + os.path.basename(get_tarball_uri(package).rstrip(".tar")))
    else:
        return(globalvars.SUBSTITUTION_MAP['rbuild_const_dir'] + '/' + package)

def prepare_env(env, package):
    environ = os.environ.copy()
    env_add = []
    if env in conf.config['default']:
        for v in conf.get_config_value('default', env).split(', '):
           if v.count('|') != 1:
                die("Error: Invalid default environment variable assignment \"" + v + "\"! Exiting.")
           env_add.append(v.split('|'))
    
    if package in conf.config[env + '_env']:
        for v in conf.get_config_value(env + '_env', package).split(', '):
            if v.count('|') != 1:
                die("Error: Invalid " + env + " environment variable assignment \"" + v + "\" for package \"" + package + "\"! Exiting.")
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

def patch_source(package):
    patches = conf.get_config_value('patches', package).split(", ")
    patchdir = globalvars.SUBSTITUTION_MAP['rbuild_patches_dir'] + '/' + package
    i = 0
    for uri in patches:
        filename = os.path.basename(uri)
        absolute_path = patchdir + '/' + filename
        verbose_output("Patching source of " + package + ": Applying patch " + str(i) + "... ")
        cmd = "patch -i " + absolute_path
        r = do_shell_cmd(cmd, get_wrkdir(package), None)
        if r != 0:
            die("\nError applying patch \"" + absolute_path + "\"! Exiting.")
        verbose_output("ok\n")
        i = i + 1

def main():
    print("This module is meant to be used with MiniRaven and not really useful on it's own.")
    exit(0)

##########
 # Main #
##########

if __name__ == "__main__":
    main()

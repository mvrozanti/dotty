#!/usr/bin/env python3
from __future__ import print_function

# Copyright (C) 2015 Vibhav Pant <vibhavp@gmail.com>
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import json
import os
import shutil
import sys
import argparse
import errno

# Fix Python 2.x
try: input = raw_input
except NameError: pass

chdir_config = lambda config: os.chdir(os.path.expanduser(os.path.abspath(os.path.dirname(config))))
prompt_user = True

def run_command(command, chdir2config=None):
    if chdir2config: chdir_config(chdir2config)
    os.system(command)

def ask_user(prompt):
    valid = {'yes':True, 'y':True, '':True, 'no':False, 'n':False}
    valid_always = {'all': True, 'a':True}
    while True:
        print('{0} '.format(prompt),end='')
        choice = input().lower()
        if choice in valid: return valid[choice]
        if choice in valid_always:
            prompt_user = False
            return True
        else: print("Enter a correct choice.", file=sys.stderr)

def create_directory(path):
    exp = os.path.expanduser(path)
    if (not os.path.isdir(exp)):
        print("{0} doesnt exist, creating.".format(exp))
        os.makedirs(exp)

def create_symlink(src, dst):
    dst = os.path.expanduser(dst)
    src = os.path.abspath(src)
    broken_symlink = os.path.lexists(dst) and not os.path.exists(dst)
    if os.path.lexists(dst):
        if os.path.islink(dst) and os.readlink(dst) == src:
            print("Skipping existing {0} -> {1}".format(dst, src))
            return
        elif prompt_user or ask_user("{0} exists, delete it? [Y/a/n]".format(dst)):
            if os.path.isfile(dst) or broken_symlink or os.path.islink(dst): os.remove(dst)
            else: shutil.rmtree(dst)
        else: return
    print("Linking {0} -> {1}".format(dst, src))
    try: os.symlink(src, dst)
    except AttributeError:
        import ctypes
        symlink = ctypes.windll.kernel32.CreateSymbolicLinkW
        symlink.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
        symlink.restype = ctypes.c_ubyte
        flags = 1 if os.path.isdir(src) else 0
        symlink(dst, src, flags)

def copy_path(src, dst, backup=False):
    dst = os.path.expanduser(dst) if not backup else os.path.abspath(dst)
    src = os.path.abspath(src) if not backup else os.path.expanduser(src)
    if os.path.exists(dst):
        if not remove_path(dst): return 
    print("Copying {0} -> {1}".format(src, dst))
    if os.path.isfile(src): 
        try: shutil.copy(src, dst) 
        except Exception as e:
            if e.errno not in [errno.ENOENT, errno.ENXIO]: raise
            os.makedirs(os.path.dirname(dst))
            shutil.copy(src, dst) 
    else: 
        try: shutil.copytree(src, dst)
        except: pass

def remove_path(path):
    path = os.path.abspath(path)
    if prompt_user or ask_user("{0} exists, delete it? [Y/a/n]".format(path)):
        if os.path.isfile(path) or os.path.islink(path): os.remove(path)
        else: shutil.rmtree(path)
        return True
    else: return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="the JSON file you want to use")
    parser.add_argument("-f", "--force",   action="store_true", help="\033[1mdoes not prompt user\033[0m: replace files/folders if they already exist, removing previous directory tree")
    parser.add_argument("-b", "--backup",  action="store_true", help="run copy in reverse so that files and directories are backed up to the directory the config file is in")
    parser.add_argument("-c", "--clear",   action="store_true", help="clears the config directory before anything, removing all files listed in it")
    parser.add_argument("-r", "--restore", action="store_true", help="restore all elements to system (mkdirs, link, copy, install(install_cmd), commands)")
    parser.add_argument("-e", "--eject",   metavar='LOCATION',  help="run --clear and move config folder to another location (thank hoberto) [TODO]")
    parser.add_argument("-d", "--dryrun",  action="store_true", help="perform a dry run, outputting what changes would have been made if this argument was removed [TODO]")
    args = parser.parse_args()
    prompt_user = not args.replace
    js = json.load(open(args.config))
    chdir_config(args.config)
    if args.eject:
        print('TO BE IMPLEMENTED')
        return 
    if args.clear:
        [remove_path(src) for src, _ in js['copy'].items()]
    if args.backup: 
        [copy_path(src, dst, backup=True) for dst, src in js['copy'].items()] 
    if args.restore: 
        if 'mkdirs' in js: [create_directory(path) for path in js['mkdirs']]
        if 'link' in js: [create_symlink(src, dst) for src, dst in js['link'].items()]
        if 'copy' in js: [copy_path(src, dst) for src, dst in js['copy'].items()]
        if 'install' in js and 'install_cmd' in js:
            packages = ' '.join(js['install'])
            run_command("{0} {1}".format(js['install_cmd'], packages), chdir2config=chdir_config)
        if 'commands' in js: [run_command(command) for command in js['commands']]
    print("Done")

if __name__ == "__main__": main()

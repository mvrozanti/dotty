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
import os.path as op

# Fix Python 2.x
try: input = raw_input
except NameError: pass

chdir_dotfiles = lambda config: os.chdir(
            op.join(op.expanduser(op.dirname(config)), os.pardir))
prompt_user = True
dry_run = False

def run_command(command, chdir2config=None):
    if chdir2config: chdir_dotfiles(chdir2config)
    os.system(command)

def ask_user(prompt): # this could have less lines
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
    exp = op.expanduser(path)
    if (not op.isdir(exp)):
        print("{0} doesnt exist, creating.".format(exp))
        os.makedirs(exp)

def create_symlink(src, dst):
    dst = op.expanduser(dst)
    src = op.abspath(src)
    broken_symlink = op.lexists(dst) and not op.exists(dst)
    if op.lexists(dst):
        if op.islink(dst) and os.readlink(dst) == src:
            print("Skipping existing {0} -> {1}".format(dst, src))
            return
        elif prompt_user or ask_user("{0} exists, delete it? [Y/a/n]".format(dst)):
            if op.isfile(dst) or broken_symlink or op.islink(dst): os.remove(dst)
            else: shutil.rmtree(dst)
        else: return
    print("Linking {0} -> {1}".format(dst, src))
    try: os.symlink(src, dst)
    except AttributeError:
        import ctypes
        symlink = ctypes.windll.kernel32.CreateSymbolicLinkW
        symlink.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
        symlink.restype = ctypes.c_ubyte
        flags = 1 if op.isdir(src) else 0
        symlink(dst, src, flags)

def copy_path(src, dst, backup=False):
    dst = op.expanduser(dst) if not backup else op.abspath(dst)
    src = op.abspath(src) if not backup else op.expanduser(src)
    if op.exists(dst):
        if not remove_path(dst): return 
    print("Copying {0} -> {1}".format(src, dst))
    if op.isfile(src): 
        try: shutil.copy(src, dst) 
        except Exception as e:
            if e.errno not in [errno.ENOENT, errno.ENXIO]: raise
            os.makedirs(op.dirname(dst))
            shutil.copy(src, dst) 
    else: 
        try: shutil.copytree(src, dst)
        except: pass

def remove_path(path):
    path = op.abspath(path)
    if prompt_user or ask_user("{0} exists, delete it? [Y/a/n]".format(path)):
        if op.isfile(path) or op.islink(path): os.remove(path)
        else: shutil.rmtree(path)
        return True
    else: return False

def move(src, dst):
    dst = op.abspath(dst)
    doit = lambda: shutil.move(src,dst) 
    if op.exists(dst):
        if remove_path(dst): doit()
    else: doit()
            

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", metavar='*dotty*.json',       help="the JSON file you want to use, \n\
            it's only required if filename doesn't end in json or doesn't contain dotty in the basename", required=False)
    parser.add_argument("-f", "--force",   action="store_true", help="\033[1mdoes not prompt user\033[0m: replace files/folders if they already exist, removing previous directory tree")
    parser.add_argument("-b", "--backup",  action="store_true", help="run copy in reverse so that files and directories are backed up to the directory the config file is in", default=len(sys.argv) > 2)
    parser.add_argument("-c", "--clear",   action="store_true", help="clears the config directory before anything, removing all files listed in it")
    parser.add_argument("-r", "--restore", action="store_true", help="restore all elements to system (mkdirs, link, copy, install(install_cmd), commands)")
    parser.add_argument("-d", "--dryrun",  action="store_true", help="perform a dry run, outputting what changes would have been made if this argument was removed [TODO]")
    parser.add_argument("-e", "--eject",   metavar='LOCATION',  help="run --clear and move config folder to another location (thank hoberto)")
    args = parser.parse_args()
    origin_dir = os.getcwd()
    prompt_user = not args.force
    if not args.config: # look in parent directory of this script
        dir_path = op.dirname(op.realpath(__file__))
        for f in os.listdir(dir_path):
            basename = op.basename(f)
            if all(name in basename for name in ['dotty','json']): 
               args.config = op.join(dir_path, f)
               print('Found dotty configuration')
    if args.config is None: raise Exception('JSON config file is missing, add it to this script\'s folder')
    js = json.load(open(args.config))
    chdir_dotfiles(args.config) 
    if args.clear or args.eject:
        for f in os.listdir(op.join(op.dirname(args.config), os.pardir)):
            if not any(name in op.basename(f) for name in ['dotty','.git']): remove_path(f)
    if args.eject:
        os.chdir(origin_dir)
        if not op.exists(args.eject): 
            args.eject = op.realpath(args.eject)
            print('{0} does not exist. Would you like to create it? [Y/n]'.format(args.eject))
            if input().lower() in ['y', 'yes', '']: os.makedirs(args.eject)
            else: raise Exception('Unable to eject') 
        if op.exists(args.eject) and op.isdir(args.eject):
            for f in os.listdir(os.getcwd()):
                if 'test' not in op.basename(f): shutil.move(op.realpath(f), args.eject)
        return 
    if args.backup: 
        [copy_path(src, dst, backup=True) for dst, src in js['copy'].items()] 
    if args.restore: 
        if 'mkdirs' in js: [create_directory(path) for path in js['mkdirs']]
        if 'link' in js: [create_symlink(src, dst) for src, dst in js['link'].items()]
        if 'copy' in js: [copy_path(src, dst) for src, dst in js['copy'].items()]
        if 'install' in js and 'install_cmd' in js:
            packages = ' '.join(js['install'])
            run_command("{0} {1}".format(js['install_cmd'], packages), chdir2config=chdir_dotfiles)
        if 'commands' in js: [run_command(command) for command in js['commands']]
    print("Done")

if __name__ == "__main__": main()

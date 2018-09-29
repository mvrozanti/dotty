#!/usr/bin/env python3
import json
import os
import shutil
import sys
import argparse
import errno
import os.path as op
import glob
import subprocess

try: input = raw_input # Fix Python 2.x
except NameError: pass

SAFE_NAMES = ['dotty','.git', '.git', 'README', 'LICENSE'] # maybe this should be part of config?
chdir_dotfiles = lambda config: os.chdir(op.dirname(config))
prompt_user, dry_run = True, False
dry_run_events = []

def run_command(command, chdir2dot=None):
    if chdir2dot: chdir_dotfiles(chdir2dot)
    if dry_run: dry_run_events.append(command) 
    else: os.system(command)

def ask_user(prompt):
    valid = ['yes', 'y', '']
    valid_always = ['all', 'a']
    invalid = ['n', 'no']
    while True:
        print('{0} '.format(prompt),end='')
        choice = input().lower()
        if choice in valid_always: 
            global prompt_user
            prompt_user = False
        if choice in valid or valid_always: return True
        elif choice in invalid: return False
        else: 
            print("Enter a correct choice.", file=sys.stderr)
            ask_user(prompt)

def create_directory(path):
    exp = op.expanduser(path)
    if dry_run: 
        dry_run_events.append('mkdir: {0}'.format(exp)) 
        return 
    if (not op.isdir(exp)):
        print('{0} doesnt exist, creating.'.format(exp))
        os.makedirs(exp)

def create_symlink(src, dst):
    dst = op.expanduser(dst)
    src = op.abspath(src)
    broken_symlink = op.lexists(dst) and not op.exists(dst)
    if op.lexists(dst):
        if op.islink(dst) and os.readlink(dst) == src:
            if not dry_run: print('Skipping existing {0} -> {1}'.format(dst, src))
            return
        elif dry_run or prompt_user or ask_user('{0} exists, delete it? [Y/a/n]'.format(dst)):
            if dry_run: dry_run_events.append('remove: {0}'.format(dst))
            else:
                if op.isfile(dst) or broken_symlink or op.islink(dst): os.remove(dst)
                else: shutil.rmtree(dst)
        else: return
    if not dry_run: print("Linking {0} -> {1}".format(dst, src))
    if dry_run: 
        dry_run_events.append('symlink: {0} -> {1}'.format(src, dst)) 
        return 
    try: os.symlink(src, dst)
    except AttributeError:
        import ctypes
        symlink = ctypes.windll.kernel32.CreateSymbolicLinkW
        symlink.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
        symlink.restype = ctypes.c_ubyte
        flags = 1 if op.isdir(src) else 0
        symlink(dst, src, flags)

def copypath(src, dst, backup=False):
    dst = op.expanduser(dst) if not backup else op.abspath(dst)
    src = op.abspath(src) if not backup else op.expanduser(src)
    if '*' in src: 
        [copypath(path, dst, backup=backup) for path in glob.glob(src)]
        return 
    if op.exists(dst) and not remove_path(dst): return 
    if dry_run: 
        dry_run_events.append('copy: {0} -> {1}'.format(src, dst)) 
        return 
    else: print("Copying {0} -> {1}".format(src, dst))
    if op.isfile(src): 
        try: shutil.copy(src, dst) 
        except Exception as e:
            if e.errno not in [errno.ENOENT, errno.ENXIO]: raise
            os.makedirs(op.dirname(dst))
            shutil.copy(src, dst) 
    else: 
        try: shutil.copytree(src, dst)
        except: pass

def remove_path(path, force=False):
    path = op.abspath(path)
    if dry_run: 
        dry_run_events.append('remove: {0}'.format(path)) 
        return 
    if force or not prompt_user or ask_user('{0} exists, delete it? [Y/a/n]'.format(path)):
        if op.isfile(path) or op.islink(path): os.remove(path)
        else: shutil.rmtree(path)
        return True
    else: return False

def main():
    global dry_run,prompt_user
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", metavar='*dotty*.json',     help="the JSON file you want to use, \n\
            it's only required if filename doesn't end in json or doesn't contain dotty in the basename", required=False)
    parser.add_argument("-f", "--force",   action='store_true', help="\033[1mdo not prompt user\033[0m: replace files/folders if they already exist, removing previous directory tree")
    parser.add_argument("-b", "--backup",  action='store_true', help="run copy in reverse so that files and directories are backed up to the directory the config file is in")
    parser.add_argument("-c", "--clear",   action='store_true', help="clears the config directory before anything, removing all files listed in it")
    parser.add_argument("-r", "--restore", action='store_true', help="restore all elements to system (mkdirs, link, copy, install(install_cmd), commands)")
    parser.add_argument("-d", "--dry-run", action='store_true', help="perform a dry run, outputting what changes would have been made if this argument was removed [TODO]")
    parser.add_argument("-s", "--sync",    nargs='*',           help="perform action --backup, commits changes and pushes to the dotfiles remote repository (must already be set up) and then --clear", metavar='commit message')
    parser.add_argument("-e", "--eject",   metavar='LOCATION',  help="run --clear and move contents of dotfiles folder to another folder (thank hoberto)")
    parser.add_argument("-i", "--inspect", action='store_true', help="show differences between the last commit and the one before that [TODO]")
    args = parser.parse_args()
    origin_dir = os.getcwd()
    dry_run = args.dry_run
    prompt_user = not args.force
    if not args.config: # look in parent directory of this script
        dir_path = op.abspath(op.join(op.dirname(op.realpath(__file__)), op.pardir))
        for f in os.listdir(dir_path):
            basename = op.basename(f)
            if all(name in basename for name in ['dotty','json']): 
               args.config = op.join(dir_path, f)
               print('Found dotty configuration at {}'.format(args.config))
    if args.config is None: raise Exception('JSON config file is missing, add it to this script\'s folder')
    js = json.load(open(args.config))
    chdir_dotfiles(args.config) 
    def clear_dotfiles(force=False):
        if force  or input('This is about to clear the dotfiles directory, are you sure you want to proceed? [y/N] ') == 'y':
            chdir_dotfiles(args.config) 
            dotfiles_dir = op.dirname(args.config)
            for f in [op.abspath(f) for f in os.listdir(dotfiles_dir)]:
                if not any(name in op.basename(f) for name in SAFE_NAMES): remove_path(op.abspath(f), force=force)
        else: return 
    if args.clear or args.eject: clear_dotfiles(force=False)
    if args.eject:
        op.chdir(origin_dir)
        if not op.exists(args.eject): 
            args.eject = op.realpath(args.eject)
            print('{0} does not exist. Would you like to create it? [Y/n]'.format(args.eject)) # maybe use ask_user?
            if input().lower() in ['y', 'yes', '']: os.makedirs(args.eject)
            else: raise Exception('Unable to eject') 
        if op.exists(args.eject) and op.isdir(args.eject):
            for f in os.listdir(os.getcwd()): shutil.move(op.realpath(f), args.eject)
    if args.backup or args.sync is not None and 'copy' in js: [copypath(src, dst, backup=True) for dst, src in js['copy'].items()] 
    if args.restore and 'copy' in js:
        if os.geteuid() != 0: subprocess.check_call("sudo -v -p '[sudo] password for %u: '", shell=True) 
        # or print('Could not escalate priviledges. Exiting') or sys.exit(1)
        if 'install' in js and 'install_cmd' in js: run_command("{0} {1}".format(js['install_cmd'], ' '.join(js['install'])), chdir2dot=args.config)
        if 'mkdirs' in js: [create_directory(path) for path in js['mkdirs']]
        if 'link' in js: [create_symlink(src, dst) for src, dst in js['link'].items()]
        if 'copy' in js: [copypath(src, dst) for src, dst in js['copy'].items()]
        if 'commands' in js: [run_command(command) for command in js['commands']]
    if args.sync is not None and 'copy' in js:
        chdir_dotfiles(args.config)
        run_command('git add .')
        commit_message = ' '.join(args.sync) # join arguments as commit message
        if not dry_run and not args.force and not commit_message: commit_message = input('Please enter commit message for this change: ')
        run_command('git commit -m "{0}"'.format(commit_message))
        run_command('git diff HEAD^ HEAD')
        run_command('git push {0}'.format('-f' if args.force else ''))
        clear_dotfiles(force=True)
    if args.dry_run: 
        for evt in dry_run_events: print(evt)
    if args.inspect: chdir_dotfiles(args.config)

if __name__ == "__main__": main()
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

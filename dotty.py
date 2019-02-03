#!/usr/bin/env python3
import code
import getpass
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
    try:
        if chdir2dot: chdir_dotfiles(chdir2dot)
        if dry_run: dry_run_events.append(command)
        else: os.system(command)
    except Exception as e: print(e)

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

def check_sudo(msg=None):
    if getpass.getuser() == 'root' and input('Copying files as root can be dangerous. Proceed? [y/N]').lower() not in ['y', 'yes']: sys.exit(1)
    if os.geteuid():
        if msg: print(msg)
        if subprocess.check_call("sudo -v -p '[sudo] password for %u: '", shell=True):
            print('Couldn\'t authenticate')
            sys.exit(1)

def create_directory(path):
    exp = op.expanduser(path)
    if dry_run:
        dry_run_events.append('would mkdir: {0}'.format(exp))
        return
    if not op.isdir(exp):
        print('{0} doesnt exist, creating.'.format(exp))
        os.makedirs(exp)

def create_symlink(src, dst):
    dst = op.expanduser(dst)
    src = op.abspath(src)
    broken_symlink = op.lexists(dst) and not op.exists(dst)
    if op.lexists(dst):
        if op.islink(dst) and os.readlink(dst) == src:
            if not dry_run: print('would skip existing symlink {0} -> {1}'.format(dst, src))
            return
        elif dry_run or prompt_user or ask_user('{0} exists, delete it? [Y/a/n]'.format(dst)):
            if dry_run: dry_run_events.append('remove: {0}'.format(dst))
            else:
                if op.isfile(dst) or broken_symlink or op.islink(dst): os.remove(dst)
                else: shutil.rmtree(dst)
        else: return
    if not dry_run: print("Linking {0} -> {1}".format(dst, src))
    if dry_run:
        dry_run_events.append('would symlink: {0} -> {1}'.format(src, dst))
        return
    try: os.symlink(src, dst)
    except AttributeError:
        import ctypes
        symlink = ctypes.windll.kernel32.CreateSymbolicLinkW
        symlink.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
        symlink.restype = ctypes.c_ubyte
        flags = 1 if op.isdir(src) else 0
        symlink(dst, src, flags)

def copypath(src, dst, excluded=[], backup=False):
    if op.basename(src) in excluded or op.basename(dst) in excluded: return
    dst = op.expanduser(dst) if not backup else op.abspath(dst)
    src = op.abspath(src) if not backup else op.expanduser(src)
    if '*' in src:
#        if '*' in dst and backup:
#             result1 = ''
#             result2 = ''
#             globbed_src = None
#             if not glob.glob(dst):
#                 try: globbed_src = glob.glob(src)[0]
#                 except Exception as e:
#                     print('File not found: ' + src)
#                     return
#                 maxlen=len(src) if len(globbed_src)<len(src) else len(globbed_src)
#                 for i in range(maxlen):
#                   letter1=globbed_src[i:i+1]
#                   letter2=src[i:i+1]
#                   if letter1 != letter2:
#                     result1+=letter1
#                     result2+=letter2
#                 dst = dst.replace(result2, result1)
        try:
            [copypath(path, dst, backup=backup) for path in glob.glob(src)]
        except Exception as e: print(e)
        finally: return
    if op.exists(dst) and not remove_path(dst, force=backup): return
    if dry_run:
        dry_run_events.append('would copy: %100s -> %s' % (src, dst))
        return
    if op.isfile(src):
        if not dry_run: print("Copying %100s -> %s" % (src, dst))
        try: shutil.copy(src, dst)
        except Exception as e:
            if e.errno == errno.EPERM or e.errno == errno.EACCES:
                print(src, '->', dst)
                subprocess.run(['sudo', 'cp', src, dst])
            else:
                os.makedirs(op.dirname(dst))
                shutil.copy(src, dst)
    else:
        try: shutil.copytree(src, dst)
        except: pass

def remove_path(path, excluded=[], force=False):
    try:
        path = op.abspath(path)
        if op.basename(path) in excluded: return
        if dry_run:
            dry_run_events.append('remove: {0}'.format(path))
            return
        if force or not prompt_user or ask_user('{0} exists, delete it? [Y/a/n]'.format(path)):
            if op.isfile(path) or op.islink(path):
                try: os.remove(path)
                except Exception as e:
                    if e.errno == errno.EACCES or e.errno.EPERM:
                        print('About to delete %s' % path)
                        subprocess.run(['sudo','rm',path])
                        # check_sudo('About to delete %s' % path)
                        # remove_path(path) # not sure why this wont work; we have check_sudo
            else: shutil.rmtree(path)
            return True
        else: return False
    except Exception as e: print(e)

def main():
    global dry_run,prompt_user
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", metavar='*dotty*.json',     help="the JSON file you want to use, \n\
            it's only required if filename doesn't end in json or doesn't contain dotty in the basename", required=False)
    parser.add_argument("-f", "--force",   action='store_true', help="\033[1mdo not prompt user\033[0m: replace files/folders if they already exist, removing previous directory tree")
    parser.add_argument("-b", "--backup",  action='store_true', help="run copy in reverse so that files and directories are backed up to the directory the config file is in")
    parser.add_argument("-c", "--clear-b", action='store_true', help="clears the config directory before any operations, removing all files listed in it")
    parser.add_argument("-C", "--clear-a", action='store_true', help="clears the config directory after every operation, removing all files listed in it")
    parser.add_argument("-r", "--restore", action='store_true', help="restore all elements to system (mkdirs, link, copy, install(install_cmd), commands)")
    parser.add_argument("-d", "--dry-run", action='store_true', help="perform a dry run, outputting what changes would have been made if this argument was removed [TODO]")
    parser.add_argument("-s", "--sync",    nargs='*',           help="perform action --backup, commits changes and pushes to the dotfiles remote repository (must already be set up) and then --clear-a", metavar='commit message')
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
    excluded = js['excluded'] if 'excluded' in js else []
    def clear_dotfiles(force=False, excluded=[]):
        if force or input('This is about to clear the dotfiles directory, are you sure you want to proceed? [y/N] ') == 'y':
            chdir_dotfiles(args.config)
            dotfiles_dir = op.dirname(args.config)
            for f in [op.abspath(f) for f in os.listdir(dotfiles_dir)]:
                basename = op.basename(f)
                if not any(name in basename for name in SAFE_NAMES) and not any(name in basename for name in excluded): remove_path(op.abspath(f), force=force)
        else: return
    if args.clear_b or args.eject: clear_dotfiles(excluded=excluded, force=args.clear_b)
    if args.eject:
        op.chdir(origin_dir)
        if not op.exists(args.eject):
            args.eject = op.realpath(args.eject)
            print('{0} does not exist. Would you like to create it? [Y/n]'.format(args.eject)) # maybe use ask_user?
            if input().lower() in ['y', 'yes', '']: os.makedirs(args.eject)
            else: raise Exception('Unable to eject')
        if op.exists(args.eject) and op.isdir(args.eject):
            for f in os.listdir(os.getcwd()): shutil.move(op.realpath(f), args.eject)
    if args.backup or args.sync is not None and 'copy' in js:
        [run_command(command) for command in js['before_bak']]
        [copypath(src, dst, excluded=excluded, backup=True) for dst, src in js['copy'].items() if dst[0] != '_' and src[0] != '_']
    if args.restore:
        check_sudo()
        if 'install' in js and 'install_cmd' in js:
            for c in js['install']:
                if c[0] != '_': run_command("command -v {1} || {0} {1}".format(js['install_cmd'], c), chdir2dot=args.config)
        if 'commands' in js: [run_command(command) for command in js['commands'] if command[0] != '_']
        if 'mkdirs' in js: [create_directory(path) for path in js['mkdirs']]
        if 'link' in js: [create_symlink(src, dst) for src, dst in js['link'].items() if dst[0] != '_' and src[0] != '_']
        if 'copy' in js: [copypath(src, dst, excluded=excluded) for src, dst in js['copy'].items() if dst[0] != '_' and src[0] != '_']
        run_command('git submodule update')
    if args.sync is not None and 'copy' in js:
        chdir_dotfiles(args.config)
        run_command('git submodule update --recursive --remote')
        run_command('git add .')
        commit_message = ' '.join(args.sync) # join arguments as commit message
        if not dry_run and not args.force and not commit_message: commit_message = input('Please enter commit message for this change: ')
        run_command('git commit -m "{0}"'.format(commit_message))
        run_command('git diff HEAD^ HEAD')
        run_command('git push {0}'.format('-f' if args.force else ''))
    if args.dry_run:
        for evt in dry_run_events: print(evt)
    if args.inspect: chdir_dotfiles(args.config)
    if not args.dry_run and args.clear_a: clear_dotfiles()

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

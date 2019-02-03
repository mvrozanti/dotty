## Dotty is a script for syncing and managing versions of your dotfiles.

### Usage
[![asciicast](https://asciinema.org/a/200410.png)](https://asciinema.org/a/200410)

### Installation
  Add dotty to your dotfiles' git repository:

    cd ~/chosen-dotfiles-folder; [[ -f .git ]] || git init
    git submodule add https://github.com/mvrozanti/dotty \
     git submodule update --remote dotty

  Optionally, you can copy the sample config file to your dotfiles directory with:

    cp dotty/dotty-sample-config.json .

You're done!

### Configuration
  Dotty uses a JSON-formatted config located on the dotfiles directory. "Comments" can be made starting with \_.
  Currently, dotty can create/check with `mkdirs`, `link` or `copy` files/directories, `install` packages and execute shell `commands`.

  It is also capable of automatically pushing changes made to your dotfiles to remote repositories with the `-s` or `--sync` flag.

  Most importantly, it can also restore the dotfiles to their respective locations on the target file system. That is, you can take your files *and* your configurations anywhere, while backing it up remotely if desired.

### Restoring dotfiles
  Make sure to clone recursively so `dotty` and other submodules are cloned as well:

    git clone --recursive https://github.com/<username>/<repository>
    ./dotty/dotty.py -s

  This will start a `--sync` process as is shown in the first section of this README


### Features
- Link-following
- Unix shell-style wildcards (globbing) in `copy` paths
- Support for git submodules

### Parameters

    usage: dotty.py [-h] [--config *dotty*.json] [-f] [-b] [-c] [-C] [-r] [-d]
                    [-s [commit message]] [-e LOCATION] [-i]

    optional arguments:
      -h, --help            show this help message and exit
      --config *dotty*.json
                            the JSON file you want to use, it's only required if
                            filename doesn't end in json or doesn't contain dotty
                            in the basename
      -f, --force           [1mdo not prompt user[0m: replace files/folders if
                            they already exist, removing previous directory tree
      -b, --backup          run copy in reverse so that files and directories are
                            backed up to the directory the config file is in
      -c, --clear-b         clears the config directory before any operations,
                            removing all files listed in it
      -C, --clear-a         clears the config directory after every operation,
                            removing all files listed in it
      -r, --restore         restore all elements to system (mkdirs, link, copy,
                            install(install_cmd), commands)
      -d, --dry-run         perform a dry run, outputting what changes would have
                            been made if this argument was removed [TODO]
      -s [commit message [commit message ...]], --sync [commit message [commit message ...]]
                            perform action --backup, commits changes and pushes to
                            the dotfiles remote repository (must already be set
                            up) and then --clear-a
      -e LOCATION, --eject LOCATION
                            run --clear and move contents of dotfiles folder to
                            another folder (thank hoberto)
      -i, --inspect         show differences between the last commit and the one
                            before that [TODO]

### To be implemented

 - Check if any file listed in config are missing and warn user before trying to operate on them

 - Mutually exclusive arguments

 - No-op file configuration (exclude certain paths that match unix shell-style wildcards) under "noop" key

 - Check if user needs/has sudo permissions and pip running on restore

### Sample configuration

    {
        "mkdirs": ["~/.vim"],

        "link": {
            "<file in dotfiles folder>": "<file in filesystem>",
            "zshrc": "~/.zshrc",
            "emacs/lisp/": "~/.emacs.d/lisp",
            "/mnt/1ADE1465DE134C17/or/another/external/drive": "~/external/drive"
        },

        "copy": {
            "<file in dotfiles folder>": "<file in filesystem>",
            ".vimrc": "~/.vimrc",
            ".config/": "~/.config/xyz/*conf"
        },

        "install_cmd": "apt-get install",
        "install": [
            "zsh",
            "firefox",
            "vim"
        ],

        "before_bak":[
            "zip -r ~/android-studio-config.zip ~/.AndroidStudio3.2/config/*"
        ],

        "excluded": [
            "password.gpg",
            "*.gpg"
        ],

        "commands": [
            "git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim && vim +PluginInstall +qall"
        ]
    }

